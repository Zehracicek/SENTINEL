from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from auth import require_api_token
from database import get_db
from schemas import (
    AnomalyEventDetailResponse,
    AnomalyEventResponse,
    AnomalyStats,
    SensorReadingResponse,
)

router = APIRouter(prefix="/api/anomalies", tags=["Anomaliler"])


@router.get("", response_model=list[AnomalyEventResponse])
async def list_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    acknowledged: Optional[bool] = Query(
        None, description="Filter by acknowledgment status (true / false)"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_anomalies(
        db, severity=severity, skip=skip, limit=limit, acknowledged=acknowledged
    )


@router.get("/recent", response_model=list[AnomalyEventResponse])
async def recent_anomalies(db: AsyncSession = Depends(get_db)):
    return await crud.get_recent_anomalies(db, limit=10)


@router.get("/stats", response_model=list[AnomalyStats])
async def anomaly_stats(db: AsyncSession = Depends(get_db)):
    return await crud.get_anomaly_stats(db)


@router.get("/{anomaly_id}/detail", response_model=AnomalyEventDetailResponse)
async def anomaly_detail(
    anomaly_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    row = await crud.get_anomaly_with_reading(db, anomaly_id)
    if not row:
        raise HTTPException(status_code=404, detail="Anomali kaydı bulunamadı")
    event, reading = row
    base = AnomalyEventResponse.model_validate(event)
    detail = AnomalyEventDetailResponse(
        **base.model_dump(),
        reading=SensorReadingResponse.model_validate(reading) if reading else None,
    )
    return detail


@router.patch(
    "/{anomaly_id}/acknowledge",
    response_model=AnomalyEventResponse,
    dependencies=[Depends(require_api_token)],
)
async def acknowledge_anomaly(
    anomaly_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    event = await crud.acknowledge_anomaly(db, anomaly_id)
    if not event:
        raise HTTPException(status_code=404, detail="Anomali kaydı bulunamadı")
    await db.commit()
    return event
