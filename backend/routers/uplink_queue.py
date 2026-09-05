from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from database import get_db

router = APIRouter(prefix="/api/uplink-queue", tags=["Uplink kuyruğu"])


@router.get("")
async def uplink_queue_snapshot(db: AsyncSession = Depends(get_db)):
    return await crud.get_uplink_queue_snapshot(db)
