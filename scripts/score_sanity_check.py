"""Skorlama boru hattını çevrimdışı ölçer (veritabanı/sunucu gerekmez).

`edge_processor` içindeki z-score + River harmanını gerçek MSL verisi üzerinde
tekrarlar ve etiketli anomali bölgelerine karşı precision/recall üretir. River
kalibrasyonu gibi değişikliklerin etkisini sunucuyu saatlerce çalıştırmadan
görmek için kullanılır.

    python scripts/score_sanity_check.py --steps 3000
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from channel_features import KNOWN_CHANNELS  # noqa: E402
from river_learner import RiverLearner  # noqa: E402
from simulator import MSL_CHANNELS  # noqa: E402

DATA_DIR = ROOT / "backend" / "data"
THRESHOLD = 50
THRESHOLD_SWEEP = (40, 50, 60, 70, 80, 85, 90)
MAX_HISTORY = 500


def load_channels() -> dict[str, np.ndarray]:
    data = {}
    for chan in KNOWN_CHANNELS:
        path = DATA_DIR / "test" / f"{chan}.npy"
        if not path.is_file():
            raise SystemExit(
                f"{path} yok. Önce: python scripts/fetch_dataset.py"
            )
        data[chan] = np.load(path)[:, 0].astype(np.float64)
    return data


def load_labels() -> dict[str, list[tuple[int, int]]]:
    df = pd.read_csv(DATA_DIR / "labeled_anomalies.csv")
    out: dict[str, list[tuple[int, int]]] = {}
    for _, row in df.iterrows():
        if row["chan_id"] in KNOWN_CHANNELS:
            out[row["chan_id"]] = [
                (int(a), int(b)) for a, b in ast.literal_eval(row["anomaly_sequences"])
            ]
    return out


def z_style_score(history: list[float], value: float) -> float:
    if len(history) < 10:
        mean, std = 0.0, 0.3
    else:
        arr = np.asarray(history)
        mean = float(arr.mean())
        std = max(float(arr.std()), 1e-6)
    return min(100.0, abs(value - mean) / std * 25.0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=3000)
    args = parser.parse_args()

    data = load_channels()
    labels = load_labels()
    learner = RiverLearner()
    learner.reset_model()

    history: dict[str, list[float]] = defaultdict(list)
    river_samples: list[float] = []
    scored: list[tuple[float, bool]] = []

    for i in range(args.steps):
        for chan in KNOWN_CHANNELS:
            series = data[chan]
            value = float(series[i % len(series)])
            idx = i % len(series)
            # edge_processor z-score geçmişini kanal değil sensör tipi başına
            # tutar; SPEC (C-1, C-2, F-7) ve TEMP (T-1, T-2) tamponu paylaşır.
            bucket = MSL_CHANNELS[chan]["sensor_type"]

            z = z_style_score(history[bucket], value)
            river = learner.score_and_learn(chan, value)
            river_samples.append(river)
            score = 0.4 * z + 0.6 * river

            history[bucket].append(value)
            if len(history[bucket]) > MAX_HISTORY:
                history[bucket] = history[bucket][-MAX_HISTORY:]

            truth = any(a <= idx <= b for a, b in labels.get(chan, []))
            scored.append((score, truth))

    total = len(scored)
    positives = sum(1 for _, t in scored if t)
    arr = np.asarray(river_samples)

    print(f"okuma             : {total:,}")
    print(f"gercek anomali    : {positives:,} ({positives / total:.2%})")
    print(
        "river skoru       : "
        f"ort={arr.mean():.1f} medyan={np.median(arr):.1f} "
        f"p95={np.percentile(arr, 95):.1f} max={arr.max():.1f}"
    )
    print()
    print("esik  isaretlenen        TP    FP    FN  precision  recall      F1")
    for threshold in THRESHOLD_SWEEP:
        tp = sum(1 for s, t in scored if s >= threshold and t)
        fp = sum(1 for s, t in scored if s >= threshold and not t)
        fn = positives - tp
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        marker = " <- varsayilan taban" if threshold == THRESHOLD else ""
        print(
            f"{threshold:4d}  {(tp + fp) / total:9.2%}  {tp:5d} {fp:5d} {fn:5d}"
            f"     {precision:.3f}   {recall:.3f}   {f1:.3f}{marker}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
