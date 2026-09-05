import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    AnomalyEvent,
    ModelUpdate,
    OrbiterQueueItem,
    OrbiterRelayLog,
    SensorReading,
    TransmissionLog,
    UplinkQueueItem,
)
from orbiter_processor import OrbiterPacket, OrbiterProcessor
from sequence_metrics import score_sequences
from simulator import MSL_CHANNELS, get_anomaly_labels

DSN_STATIONS = ["Goldstone-DSS14", "Canberra-DSS43", "Madrid-DSS63"]


async def create_sensor_reading(db: AsyncSession, data: dict) -> SensorReading:
    reading = SensorReading(**data)
    db.add(reading)
    await db.flush()
    return reading


async def create_anomaly_event(db: AsyncSession, data: dict) -> AnomalyEvent:
    event = AnomalyEvent(**data)
    db.add(event)
    await db.flush()
    return event


async def create_transmission_log(db: AsyncSession, data: dict) -> TransmissionLog:
    log = TransmissionLog(**data)
    db.add(log)
    await db.flush()
    return log


def _reading_row_for_orm(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_")}


async def bulk_create_readings(
    db: AsyncSession,
    readings: List[dict],
    anomalies: List[dict],
    transmission: Optional[dict],
) -> None:
    for r in readings:
        row = _reading_row_for_orm(r)
        db.add(SensorReading(**row))
        if r.get("_uplink_eligible"):
            db.add(
                UplinkQueueItem(
                    reading_id=row["id"],
                    uplink_priority=float(row.get("anomaly_score", 0)),
                    status="pending",
                    queued_at=datetime.now(timezone.utc),
                )
            )
            db.add(
                OrbiterQueueItem(
                    reading_id=row["id"],
                    status="pending",
                    queued_at=datetime.now(timezone.utc),
                )
            )
    for a in anomalies:
        # `_sensor_type` / `_channel_id` yalnızca WebSocket yayını için taşınır
        db.add(AnomalyEvent(**{k: v for k, v in a.items() if not k.startswith("_")}))
    if transmission:
        db.add(TransmissionLog(**transmission))
    await db.flush()


def _reading_to_dict(r: SensorReading) -> dict:
    return {
        "id": r.id,
        "sensor_type": r.sensor_type,
        "channel_id": r.channel_id,
        "raw_value": r.raw_value,
        "unit": r.unit,
        "anomaly_score": r.anomaly_score,
        "is_anomaly": r.is_anomaly,
        "ground_truth_anomaly": r.ground_truth_anomaly,
        "is_transmitted": r.is_transmitted,
        "is_novel": getattr(r, "is_novel", False),
        "replay_index": getattr(r, "replay_index", None),
        "location_lat": r.location_lat,
        "location_lon": r.location_lon,
        "sol": r.sol,
        "created_at": r.created_at,
    }


def _queue_item_pending_dict(item: UplinkQueueItem, r: SensorReading) -> dict:
    return {
        "queue_id": str(item.id),
        "reading_id": str(r.id),
        "sensor_type": r.sensor_type,
        "anomaly_score": r.anomaly_score,
        "uplink_priority": item.uplink_priority,
        "queued_at": item.queued_at.isoformat() if item.queued_at else None,
    }


def _queue_item_sent_dict(item: UplinkQueueItem, r: SensorReading) -> dict:
    return {
        **(_queue_item_pending_dict(item, r)),
        "sent_at": item.sent_at.isoformat() if item.sent_at else None,
        "dsn_station": item.dsn_station,
    }


async def drain_uplink_queue(
    db: AsyncSession, processor: Any, max_items: int = 6
) -> List[dict]:
    stmt = (
        select(UplinkQueueItem)
        .where(UplinkQueueItem.status == "pending")
        .order_by(desc(UplinkQueueItem.uplink_priority), UplinkQueueItem.queued_at)
        .limit(max_items)
        .with_for_update(skip_locked=True)
    )
    res = await db.execute(stmt)
    items = list(res.scalars().all())
    payloads: List[dict] = []
    for item in items:
        reading = await db.get(SensorReading, item.reading_id)
        if not reading:
            item.status = "cancelled"
            continue
        reading.is_transmitted = True
        item.status = "sent"
        item.sent_at = datetime.now(timezone.utc)
        item.dsn_station = random.choice(DSN_STATIONS)
        payloads.append(_reading_to_dict(reading))
    if payloads:
        processor.record_uplink_batch(payloads)
        processor.apply_rl_rewards_after_uplink(payloads)
    await db.flush()
    return payloads


async def process_orbiter_drain(
    db: AsyncSession, orb: OrbiterProcessor, max_items: int = 24
) -> None:
    stmt = (
        select(OrbiterQueueItem)
        .where(OrbiterQueueItem.status == "pending")
        .order_by(OrbiterQueueItem.queued_at)
        .limit(max_items)
        .with_for_update(skip_locked=True)
    )
    res = await db.execute(stmt)
    items = list(res.scalars().all())
    forward_packets: List[OrbiterPacket] = []
    now = datetime.now(timezone.utc)
    for item in items:
        reading = await db.get(SensorReading, item.reading_id)
        orb.note_received(1)
        if not reading:
            item.status = "cancelled"
            continue
        if float(reading.anomaly_score) < 40.0:
            item.status = "dropped"
            orb.note_secondary_drop(1)
            continue
        item.status = "forwarded"
        item.forwarded_at = now
        forward_packets.append(
            OrbiterPacket(
                reading_id=str(reading.id),
                sol=int(reading.sol),
                anomaly_score=float(reading.anomaly_score),
                sensor_type=str(reading.sensor_type),
            )
        )
    if forward_packets:
        orb.ingest_forwarded(forward_packets)
    await db.flush()


async def insert_orbiter_relay_log(db: AsyncSession, meta: Dict[str, Any]) -> OrbiterRelayLog:
    log = OrbiterRelayLog(
        id=uuid.uuid4(),
        batch_id=UUID(meta["batch_id"]) if isinstance(meta["batch_id"], str) else meta["batch_id"],
        packets_received=int(meta["packets_received"]),
        packets_forwarded=int(meta["packets_forwarded"]),
        relay_latency_ms=float(meta["relay_latency_ms"]),
        pass_id=str(meta["pass_id"]),
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    return log


async def list_orbiter_relay_logs(
    db: AsyncSession, limit: int = 80
) -> List[OrbiterRelayLog]:
    q = (
        select(OrbiterRelayLog)
        .order_by(desc(OrbiterRelayLog.created_at))
        .limit(limit)
    )
    r = await db.execute(q)
    return list(r.scalars().all())


async def create_model_update(db: AsyncSession, payload: Dict[str, Any]) -> ModelUpdate:
    row = ModelUpdate(
        id=uuid.uuid4(),
        model_version=int(payload["model_version"]),
        threshold_suggestion=float(payload["threshold_suggestion"]),
        federated_round=int(payload["federated_round"]),
        source=str(payload.get("source", "earth_cloud")),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()
    return row


async def list_model_updates(db: AsyncSession, limit: int = 50) -> List[ModelUpdate]:
    q = select(ModelUpdate).order_by(desc(ModelUpdate.created_at)).limit(limit)
    r = await db.execute(q)
    return list(r.scalars().all())


async def get_recent_anomaly_rate(db: AsyncSession, window: int = 800) -> float:
    """Son `window` okumada anomali oranı — satırlar Python'a çekilmeden."""
    recent = (
        select(SensorReading.is_anomaly)
        .order_by(desc(SensorReading.created_at))
        .limit(window)
        .subquery()
    )
    result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(recent.c.is_anomaly.is_(True)).label("anomalies"),
        ).select_from(recent)
    )
    row = result.one()
    total = int(row.total or 0)
    if total == 0:
        return 0.0
    return int(row.anomalies or 0) / total


async def get_detection_metrics(
    db: AsyncSession, sensor_type: Optional[str] = None
) -> Dict[str, Any]:
    """Edge kararını (`is_anomaly`) veri seti etiketiyle karşılaştırır.

    `ground_truth_anomaly` yalnızca değerlendirme için saklanır; edge kararına
    girmez. Bu yüzden iki sütunun karşılaştırılması gerçek bir başarı ölçüsüdür
    (Hundman et al. makalesinin referans sonuçları değil, bu sistemin kendi
    çıktısı).
    """
    conditions = []
    if sensor_type:
        conditions.append(SensorReading.sensor_type == sensor_type)

    stmt = select(
        func.count().label("total"),
        func.count()
        .filter(
            SensorReading.is_anomaly.is_(True),
            SensorReading.ground_truth_anomaly.is_(True),
        )
        .label("tp"),
        func.count()
        .filter(
            SensorReading.is_anomaly.is_(True),
            SensorReading.ground_truth_anomaly.is_(False),
        )
        .label("fp"),
        func.count()
        .filter(
            SensorReading.is_anomaly.is_(False),
            SensorReading.ground_truth_anomaly.is_(True),
        )
        .label("fn"),
        func.count()
        .filter(
            SensorReading.is_anomaly.is_(False),
            SensorReading.ground_truth_anomaly.is_(False),
        )
        .label("tn"),
    ).select_from(SensorReading)
    if conditions:
        stmt = stmt.where(*conditions)

    row = (await db.execute(stmt)).one()
    tp, fp, fn, tn = (
        int(row.tp or 0),
        int(row.fp or 0),
        int(row.fn or 0),
        int(row.tn or 0),
    )
    total = int(row.total or 0)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    )
    # F_0.5 — Hundman et al. precision'a ağırlık veren bu ölçüyü kullanır
    beta_sq = 0.25
    f_half = (
        (1 + beta_sq)
        * precision
        * recall
        / (beta_sq * precision + recall)
        if (beta_sq * precision + recall)
        else 0.0
    )

    seq = await _sequence_detection_metrics(db, sensor_type=sensor_type)
    return {
        "sensor_type": sensor_type,
        "evaluated_readings": total,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "f_half_score": round(f_half, 4),
        "accuracy": round((tp + tn) / total, 4) if total else 0.0,
        "ground_truth_anomaly_rate": round((tp + fn) / total, 4) if total else 0.0,
        "predicted_anomaly_rate": round((tp + fp) / total, 4) if total else 0.0,
        **seq,
    }


async def _sequence_detection_metrics(
    db: AsyncSession, sensor_type: Optional[str] = None
) -> Dict[str, Any]:
    """Hundman örtüşmesi: `replay_index` olan satırlar + labeled_anomalies.csv."""
    empty = {
        "sequence_evaluated": False,
        "sequence_indexed_readings": 0,
        "sequence_true_positives": 0,
        "sequence_pred_true_positives": 0,
        "sequence_false_positives": 0,
        "sequence_false_negatives": 0,
        "sequence_true_count": 0,
        "sequence_predicted_count": 0,
        "sequence_channels_scored": 0,
        "sequence_precision": 0.0,
        "sequence_recall": 0.0,
        "sequence_f1_score": 0.0,
        "sequence_f_half_score": 0.0,
    }
    if not hasattr(SensorReading, "replay_index"):
        return empty

    conditions = [SensorReading.replay_index.is_not(None)]
    if sensor_type:
        conditions.append(SensorReading.sensor_type == sensor_type)

    count_row = (
        await db.execute(
            select(func.count()).select_from(SensorReading).where(*conditions)
        )
    ).scalar()
    indexed = int(count_row or 0)
    if indexed == 0:
        return empty

    pred_stmt = select(SensorReading.channel_id, SensorReading.replay_index).where(
        *conditions, SensorReading.is_anomaly.is_(True)
    )
    pred_rows = (await db.execute(pred_stmt)).all()
    predicted: Dict[str, List[int]] = {}
    for chan, idx in pred_rows:
        if not chan or idx is None:
            continue
        predicted.setdefault(str(chan), []).append(int(idx))

    labels = get_anomaly_labels()
    if sensor_type:
        allowed = {
            cid
            for cid, meta in MSL_CHANNELS.items()
            if meta["sensor_type"] == sensor_type
        }
        labels = {k: v for k, v in labels.items() if k in allowed}
        predicted = {k: v for k, v in predicted.items() if k in allowed}

    scored = score_sequences(predicted, labels)
    return {
        "sequence_evaluated": True,
        "sequence_indexed_readings": indexed,
        **scored,
    }


async def get_uplink_queue_snapshot(db: AsyncSession) -> Dict[str, Any]:
    ptot = await db.execute(
        select(func.count())
        .select_from(UplinkQueueItem)
        .where(UplinkQueueItem.status == "pending")
    )
    pending_total = int(ptot.scalar() or 0)
    stot = await db.execute(
        select(func.count())
        .select_from(UplinkQueueItem)
        .where(UplinkQueueItem.status == "sent")
    )
    sent_total = int(stot.scalar() or 0)

    pend = await db.execute(
        select(UplinkQueueItem, SensorReading)
        .join(SensorReading, UplinkQueueItem.reading_id == SensorReading.id)
        .where(UplinkQueueItem.status == "pending")
        .order_by(desc(UplinkQueueItem.uplink_priority), UplinkQueueItem.queued_at)
        .limit(100)
    )
    pending_rows = [
        _queue_item_pending_dict(item, r) for item, r in pend.all()
    ]

    sent = await db.execute(
        select(UplinkQueueItem, SensorReading)
        .join(SensorReading, UplinkQueueItem.reading_id == SensorReading.id)
        .where(UplinkQueueItem.status == "sent")
        .order_by(desc(UplinkQueueItem.sent_at))
        .limit(60)
    )
    sent_rows = [_queue_item_sent_dict(item, r) for item, r in sent.all()]

    return {
        "pending_total": pending_total,
        "sent_total": sent_total,
        "pending": pending_rows,
        "recent_sent": sent_rows,
    }


async def get_sensor_readings(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    sensor_type: Optional[str] = None,
) -> List[SensorReading]:
    q = select(SensorReading).order_by(desc(SensorReading.created_at))
    if sensor_type:
        q = q.where(SensorReading.sensor_type == sensor_type)
    result = await db.execute(q.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_sensor_reading_by_id(
    db: AsyncSession, reading_id: UUID
) -> Optional[SensorReading]:
    result = await db.execute(
        select(SensorReading).where(SensorReading.id == reading_id)
    )
    return result.scalar_one_or_none()


async def get_sensor_stats(db: AsyncSession) -> List[dict]:
    """Sensör tipi başına özet — tek GROUP BY sorgusu.

    Önceki sürüm her sensör tipi için 4 ayrı sorgu atıyordu (8 tip = 33 sorgu).
    """
    result = await db.execute(
        select(
            SensorReading.sensor_type,
            func.count(SensorReading.id).label("count"),
            func.avg(SensorReading.raw_value).label("mean"),
            func.stddev(SensorReading.raw_value).label("std"),
            func.count(SensorReading.id)
            .filter(SensorReading.is_anomaly.is_(True))
            .label("anomaly_count"),
        ).group_by(SensorReading.sensor_type)
    )

    stats = []
    for row in result.all():
        total = int(row.count) or 1
        stats.append(
            {
                "sensor_type": row.sensor_type,
                "count": int(row.count),
                "mean": round(float(row.mean or 0), 4),
                "std": round(float(row.std or 0), 4),
                "anomaly_rate": round(int(row.anomaly_count or 0) / total, 4),
            }
        )
    return stats


def _attach_reading_context(rows) -> List[AnomalyEvent]:
    """Okumadan gelen sensor_type / channel_id'yi olaya iliştirir.

    Mapped kolon olmadıkları için yalnızca yanıt serileştirmesinde kullanılır;
    istemci anomaliyi sensöre bağlamak için açıklama metnini aramak zorunda
    kalmaz.
    """
    events: List[AnomalyEvent] = []
    for event, sensor_type, channel_id in rows:
        event.sensor_type = sensor_type
        event.channel_id = channel_id
        events.append(event)
    return events


async def get_anomalies(
    db: AsyncSession,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    acknowledged: Optional[bool] = None,
) -> List[AnomalyEvent]:
    stmt = (
        select(AnomalyEvent, SensorReading.sensor_type, SensorReading.channel_id)
        .join(SensorReading, AnomalyEvent.reading_id == SensorReading.id)
        .order_by(desc(AnomalyEvent.created_at))
    )
    if severity:
        stmt = stmt.where(AnomalyEvent.severity == severity.upper())
    if acknowledged is not None:
        stmt = stmt.where(AnomalyEvent.acknowledged == acknowledged)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return _attach_reading_context(result.all())


async def get_anomaly_with_reading(
    db: AsyncSession, anomaly_id: UUID
) -> Optional[tuple[AnomalyEvent, Optional[SensorReading]]]:
    result = await db.execute(
        select(AnomalyEvent).where(AnomalyEvent.id == anomaly_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        return None
    reading = await db.get(SensorReading, event.reading_id)
    return event, reading


async def get_recent_anomalies(db: AsyncSession, limit: int = 10) -> List[AnomalyEvent]:
    result = await db.execute(
        select(AnomalyEvent, SensorReading.sensor_type, SensorReading.channel_id)
        .join(SensorReading, AnomalyEvent.reading_id == SensorReading.id)
        .order_by(desc(AnomalyEvent.created_at))
        .limit(limit)
    )
    return _attach_reading_context(result.all())


async def acknowledge_anomaly(
    db: AsyncSession, anomaly_id: UUID
) -> Optional[AnomalyEvent]:
    result = await db.execute(
        select(AnomalyEvent).where(AnomalyEvent.id == anomaly_id)
    )
    event = result.scalar_one_or_none()
    if event:
        event.acknowledged = True
        await db.flush()
    return event


async def get_anomaly_stats(db: AsyncSession) -> List[dict]:
    result = await db.execute(
        select(
            AnomalyEvent.anomaly_type,
            func.count(AnomalyEvent.id).label("count"),
            func.avg(AnomalyEvent.scientific_priority).label("avg_priority"),
        ).group_by(AnomalyEvent.anomaly_type)
    )
    return [
        {
            "anomaly_type": row.anomaly_type,
            "count": row.count,
            "avg_priority": round(float(row.avg_priority or 0), 2),
        }
        for row in result.all()
    ]


async def get_overview_stats(db: AsyncSession) -> dict:
    total_q = await db.execute(select(func.count(SensorReading.id)))
    total_readings = total_q.scalar() or 0

    anomaly_q = await db.execute(select(func.count(AnomalyEvent.id)))
    total_anomalies = anomaly_q.scalar() or 0

    transmitted_q = await db.execute(
        select(func.count(SensorReading.id)).where(
            SensorReading.is_transmitted == True  # noqa: E712
        )
    )
    transmitted = transmitted_q.scalar() or 0

    sev_rank = case(
        (AnomalyEvent.severity == "CRITICAL", 4),
        (AnomalyEvent.severity == "HIGH", 3),
        (AnomalyEvent.severity == "MEDIUM", 2),
        (AnomalyEvent.severity == "LOW", 1),
        else_=0,
    )
    severity_q = await db.execute(
        select(AnomalyEvent.severity)
        .order_by(desc(sev_rank), desc(AnomalyEvent.created_at))
        .limit(1)
    )
    highest = severity_q.scalar_one_or_none()

    # Bant genişliği kazancı ölçülen byte'lardan gelir: filtresiz referans
    # hacim ile gerçekten iletilen (DEFLATE sonrası) hacmin farkı. Paket
    # sayılarının oranı ayrı bir metrik olarak `packet_ratio` altında durur.
    bytes_q = await db.execute(
        select(
            func.coalesce(func.sum(TransmissionLog.baseline_bytes), 0),
            func.coalesce(func.sum(TransmissionLog.uplink_bytes), 0),
        )
    )
    baseline_bytes, uplink_bytes = bytes_q.one()
    baseline_bytes = int(baseline_bytes or 0)
    uplink_bytes = int(uplink_bytes or 0)
    total_bytes_saved = max(0, baseline_bytes - uplink_bytes)
    saved_pct = (
        round((1 - uplink_bytes / baseline_bytes) * 100, 2)
        if baseline_bytes > 0
        else 0.0
    )

    return {
        "total_readings": total_readings,
        "transmitted_readings": transmitted,
        "total_anomalies": total_anomalies,
        "bandwidth_saved_percent": saved_pct,
        "highest_severity": highest,
        "total_bytes_saved": total_bytes_saved,
        "baseline_bytes": baseline_bytes,
        "uplink_bytes": uplink_bytes,
        "packet_ratio": (
            round(transmitted / total_readings, 4) if total_readings > 0 else 0.0
        ),
    }
