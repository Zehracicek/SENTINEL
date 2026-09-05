"""NASA SMAP/MSL telemetri dosyalarını indirir (backend/data/test/*.npy).

Neden ayrı bir script: telemanom deposunun README'sinde yıllarca duran doğrudan
indirme adresi (s3-us-west-2.amazonaws.com/telemanom/data.zip) artık 403
döndürüyor ve depo Kaggle API anahtarı gerektiren bir yola geçti. Burada aynı
veriyi kimlik doğrulaması olmadan sunan HuggingFace aynası kullanılır.

Kullanım:
    python scripts/fetch_dataset.py            # 12 MSL kanalının test verisi
    python scripts/fetch_dataset.py --train    # eğitim setini de indir
    python scripts/fetch_dataset.py --lstm     # Kaggle'dan smoothed_errors + y_hat
    python scripts/fetch_dataset.py --force    # mevcut dosyaların üzerine yaz

`--lstm` için `kaggle` paketi ve `kaggle.json` gerekir. Anahtar dosyası
`KAGGLE_CONFIG_DIR` veya `~/Downloads/.kaggle` / `~/.kaggle` altında aranır.
`kaggle.json` commit edilmez ve içeriği yazdırılmaz.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
import urllib.error
import urllib.request
from pathlib import Path

REPO = "appleparan/telemanom"
BASE_URL = f"https://huggingface.co/datasets/{REPO}/resolve/main/data/data"
LABELS_URL = (
    "https://raw.githubusercontent.com/khundman/telemanom/master/labeled_anomalies.csv"
)

# backend/simulator.py MSL_CHANNELS ile aynı liste
CHANNELS = (
    "T-1",
    "T-2",
    "P-10",
    "P-14",
    "M-6",
    "M-7",
    "C-1",
    "C-2",
    "D-14",
    "D-15",
    "D-16",
    "F-7",
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "backend" / "data"


def _download(url: str, dest: Path, force: bool) -> bool:
    if dest.exists() and not force:
        print(f"atlandi (mevcut)  {dest.relative_to(ROOT)}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            tmp.write_bytes(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        tmp.unlink(missing_ok=True)
        print(f"HATA             {dest.name}: {exc}", file=sys.stderr)
        return False
    tmp.replace(dest)
    print(f"indirildi        {dest.relative_to(ROOT)}  ({dest.stat().st_size:,} B)")
    return True


KAGGLE_DATASET = "patrickfleith/nasa-anomaly-detection-dataset-smap-msl"
MODEL_DIRNAME = "2018-05-19_15.00.10"


def _default_kaggle_dir() -> Path:
    env = os.environ.get("KAGGLE_CONFIG_DIR")
    if env:
        return Path(env)
    downloads = Path.home() / "Downloads" / ".kaggle"
    if (downloads / "kaggle.json").is_file():
        return downloads
    return Path.home() / ".kaggle"


def _copy_channel_npy(src_dir: Path, dest_dir: Path, force: bool) -> int:
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for chan in CHANNELS:
        src = src_dir / f"{chan}.npy"
        dest = dest_dir / f"{chan}.npy"
        if not src.is_file():
            print(f"eksik            {src.name} ({src_dir.name})", file=sys.stderr)
            continue
        if dest.exists() and not force:
            print(f"atlandi (mevcut)  {dest.relative_to(ROOT)}")
            copied += 1
            continue
        shutil.copy2(src, dest)
        print(f"kopyalandi       {dest.relative_to(ROOT)}")
        copied += 1
    return copied


def _find_model_root(extracted: Path) -> Path | None:
    for se in extracted.rglob("smoothed_errors"):
        if se.is_dir() and (se.parent / "y_hat").is_dir():
            return se.parent
    return None


def _fetch_lstm(force: bool, config_dir: Path) -> bool:
    creds = config_dir / "kaggle.json"
    if not creds.is_file():
        print(
            "kaggle.json bulunamadı. KAGGLE_CONFIG_DIR veya "
            f"{config_dir} altına yerleştirin (içerik yazdırılmaz).",
            file=sys.stderr,
        )
        return False
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("pip install kaggle  — --lstm için gerekli.", file=sys.stderr)
        return False

    os.environ["KAGGLE_CONFIG_DIR"] = str(config_dir)
    api = KaggleApi()
    api.authenticate()

    with tempfile.TemporaryDirectory(prefix="telemanom-kaggle-") as tmp:
        tmp_path = Path(tmp)
        print("Kaggle paketi indiriliyor (yalnızca MSL LSTM çıktıları kopyalanacak)...")
        api.dataset_download_files(KAGGLE_DATASET, path=str(tmp_path), unzip=False)
        zips = list(tmp_path.glob("*.zip"))
        if not zips:
            print("Kaggle zip bulunamadı.", file=sys.stderr)
            return False
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()
        with zipfile.ZipFile(zips[0]) as zf:
            zf.extractall(extract_dir)
        model_root = _find_model_root(extract_dir)
        if model_root is None:
            print("smoothed_errors / y_hat klasörleri pakette yok.", file=sys.stderr)
            return False
        dest_root = DATA_DIR / MODEL_DIRNAME
        n_se = _copy_channel_npy(model_root / "smoothed_errors", dest_root / "smoothed_errors", force)
        n_yh = _copy_channel_npy(model_root / "y_hat", dest_root / "y_hat", force)
        if n_se < len(CHANNELS) or n_yh < len(CHANNELS):
            print("Bazı LSTM kanal dosyaları eksik kaldı.", file=sys.stderr)
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", action="store_true", help="eğitim setini de indir")
    parser.add_argument("--lstm", action="store_true", help="Kaggle LSTM çıktılarını indir")
    parser.add_argument(
        "--kaggle-dir",
        default=None,
        help="kaggle.json dizini (varsayılan: KAGGLE_CONFIG_DIR veya Downloads/.kaggle)",
    )
    parser.add_argument("--force", action="store_true", help="üzerine yaz")
    args = parser.parse_args()

    splits = ["test"] + (["train"] if args.train else [])
    ok = _download(LABELS_URL, DATA_DIR / "labeled_anomalies.csv", args.force)

    for split in splits:
        for chan in CHANNELS:
            ok &= _download(
                f"{BASE_URL}/{split}/{chan}.npy",
                DATA_DIR / split / f"{chan}.npy",
                args.force,
            )

    if args.lstm:
        kaggle_dir = Path(args.kaggle_dir) if args.kaggle_dir else _default_kaggle_dir()
        ok = _fetch_lstm(args.force, kaggle_dir) and ok

    if not ok:
        print("\nBazı dosyalar indirilemedi.", file=sys.stderr)
        return 1

    print(f"\nTamam. {len(CHANNELS)} kanal hazır: {DATA_DIR / 'test'}")
    if args.lstm:
        print(f"LSTM çıktıları: {DATA_DIR / MODEL_DIRNAME}")
    print("Backend'i yeniden başlatın; /health uç noktası durumu gösterir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
