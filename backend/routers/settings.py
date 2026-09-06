"""Çalışma anı ayarları (Groq düşünce modu vb.)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import require_api_token

router = APIRouter(prefix="/api/settings", tags=["Ayarlar"])


def _processor():
    import main as main_mod

    return main_mod.processor


class RoverThinkingBody(BaseModel):
    enabled: bool


@router.get("/rover-thinking")
async def get_rover_thinking():
    p = _processor()
    return {"enabled": p.rover_thinking_enabled}


@router.patch("/rover-thinking", dependencies=[Depends(require_api_token)])
async def patch_rover_thinking(body: RoverThinkingBody):
    p = _processor()
    p.rover_thinking_enabled = bool(body.enabled)
    from runtime_settings import save_thinking_enabled

    save_thinking_enabled(p.rover_thinking_enabled)
    return {"enabled": p.rover_thinking_enabled}
