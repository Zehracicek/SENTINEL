"""Hundman et al. (KDD 2018) tarzı dizi-seviyesi değerlendirme.

Nokta TP/FP, uzun etiketlenmiş aralıkları şişirir. Makale bir gerçek
diziyi, tahmini anomali noktası örtüşürse TP sayar; precision ise örtüşen
tahmin dizilerine bakılır.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

Interval = Tuple[int, int]


def collapse_indices_to_sequences(indices: Iterable[int]) -> List[Interval]:
    ordered = sorted({int(i) for i in indices})
    if not ordered:
        return []
    seqs: List[Interval] = []
    start = prev = ordered[0]
    for idx in ordered[1:]:
        if idx == prev + 1:
            prev = idx
        else:
            seqs.append((start, prev))
            start = prev = idx
    seqs.append((start, prev))
    return seqs


def intervals_overlap(a: Interval, b: Interval) -> bool:
    return not (a[1] < b[0] or b[1] < a[0])


def score_sequences(
    predicted_indices_by_channel: Dict[str, Sequence[int]],
    true_sequences_by_channel: Dict[str, Sequence[Interval]],
) -> Dict[str, float]:
    """Kanal bazında örtüşme; kanallar toplanır.

    `true_positives` = en az bir tahminle örtüşen gerçek diziler
    `pred_true_positives` = en az bir gerçek diziyle örtüşen tahmin dizileri
    `false_positives` = örtüşmeyen tahmin dizileri
    `false_negatives` = örtüşmeyen gerçek diziler
    """
    true_tp = 0
    pred_tp = 0
    fp = 0
    fn = 0
    pred_seq_total = 0
    true_seq_total = 0
    channels_scored = 0

    channels = sorted(
        set(predicted_indices_by_channel) | set(true_sequences_by_channel)
    )
    for chan in channels:
        true_seqs = [tuple(s) for s in true_sequences_by_channel.get(chan, [])]
        pred_seqs = collapse_indices_to_sequences(
            predicted_indices_by_channel.get(chan, [])
        )
        if not true_seqs and not pred_seqs:
            continue
        channels_scored += 1
        true_seq_total += len(true_seqs)
        pred_seq_total += len(pred_seqs)

        matched_true = set()
        matched_pred = set()
        for i, ps in enumerate(pred_seqs):
            for j, ts in enumerate(true_seqs):
                if intervals_overlap(ps, ts):
                    matched_pred.add(i)
                    matched_true.add(j)

        true_tp += len(matched_true)
        pred_tp += len(matched_pred)
        fn += len(true_seqs) - len(matched_true)
        fp += len(pred_seqs) - len(matched_pred)

    precision = pred_tp / (pred_tp + fp) if (pred_tp + fp) else 0.0
    recall = true_tp / (true_tp + fn) if (true_tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    )
    beta_sq = 0.25
    f_half = (
        (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)
        if (beta_sq * precision + recall)
        else 0.0
    )
    return {
        "sequence_true_positives": true_tp,
        "sequence_pred_true_positives": pred_tp,
        "sequence_false_positives": fp,
        "sequence_false_negatives": fn,
        "sequence_true_count": true_seq_total,
        "sequence_predicted_count": pred_seq_total,
        "sequence_channels_scored": channels_scored,
        "sequence_precision": round(precision, 4),
        "sequence_recall": round(recall, 4),
        "sequence_f1_score": round(f1, 4),
        "sequence_f_half_score": round(f_half, 4),
    }
