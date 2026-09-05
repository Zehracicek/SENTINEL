"""Edge anomali kararının veri seti etiketine göre başarı ölçümü."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from database import get_db
from simulator import get_dataset_status

router = APIRouter(prefix="/api/evaluation", tags=["Değerlendirme"])


@router.get("/detection")
async def detection_metrics(
    sensor_type: Optional[str] = Query(
        None, max_length=10, description="Örn. TEMP, CH4 — verilirse tek tip için"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Bu sistemin kendi precision/recall değerleri.

    `is_anomaly` uçta yalnızca skor tabanlı üretilir; `ground_truth_anomaly`
    veri setinin `labeled_anomalies.csv` etiketidir ve karara katılmaz. Dönen
    değerler bu iki sütunun karşılaştırmasıdır — Hundman et al. (KDD 2018)
    makalesinin referans skorlarıyla karıştırılmamalıdır.
    """
    metrics = await crud.get_detection_metrics(db, sensor_type=sensor_type)
    dataset = get_dataset_status()
    lstm = dataset["anomaly_score_source"].startswith("lstm")
    seq_ready = bool(metrics.get("sequence_evaluated"))
    note_parts = [
        "Kendi ölçümümüz; Hundman et al. (KDD 2018) makale skoru değil.",
        (
            "Skor kaynağı LSTM smoothed error + River."
            if lstm
            else "Skor kaynağı z-score + River (smoothed_errors yok)."
        ),
    ]
    if seq_ready:
        note_parts.append(
            "Dizi metrikleri Hundman örtüşmesidir: gerçek dizi TP sayılır "
            "eğer herhangi bir tahmin noktası aralığa düşerse."
        )
    else:
        note_parts.append(
            "Dizi metrikleri için replay_index gerekir (migration 008 + yeni okumalar)."
        )
    return {
        **metrics,
        "anomaly_score_source": dataset["anomaly_score_source"],
        "note": " ".join(note_parts),
    }
