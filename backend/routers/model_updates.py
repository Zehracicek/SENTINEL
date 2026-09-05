from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from database import get_db
from schemas import ModelUpdateResponse

router = APIRouter(prefix="/api/model-updates", tags=["Model güncellemeleri"])


@router.get("", response_model=list[ModelUpdateResponse])
async def list_updates(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    rows = await crud.list_model_updates(db, limit=limit)
    return rows
