from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from database import get_db
from schemas import OrbiterRelayLogResponse

router = APIRouter(prefix="/api/orbiter-log", tags=["Orbiter günlüğü"])


@router.get("", response_model=list[OrbiterRelayLogResponse])
async def list_orbiter_logs(
    limit: int = Query(80, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    rows = await crud.list_orbiter_relay_logs(db, limit=limit)
    return rows
