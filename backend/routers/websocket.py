"""Canlı WS: sensor_reading, anomaly_alert, stats_update, rover_thinking, …"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket canlı akış"])

active_connections: Set[WebSocket] = set()


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _serialize(data: dict) -> str:
    return json.dumps(data, cls=UUIDEncoder)


async def broadcast(message: dict) -> None:
    """Tüm istemcilere paralel yayın.

    Küme üzerinde doğrudan dönerken `await` yapmak, aynı anda bağlanan bir
    istemci yüzünden "Set changed size during iteration" hatasına yol açıyordu;
    bu yüzden anlık bir kopya üzerinde çalışılır. Gönderimler paralel yapılır,
    böylece tek bir yavaş istemci tüm yayını geciktirmez.
    """
    targets = list(active_connections)
    if not targets:
        return
    payload = _serialize(message)
    results = await asyncio.gather(
        *(ws.send_text(payload) for ws in targets), return_exceptions=True
    )
    for ws, result in zip(targets, results, strict=True):
        if isinstance(result, Exception):
            active_connections.discard(ws)


@router.websocket("/ws/live-feed")
async def live_feed(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Normal istemci ayrılması
        pass
    except Exception:
        # Protokol/uygulama hataları sessiz kalmasın; bağlantı yine temizlenir.
        logger.exception("WebSocket bağlantısı beklenmeyen bir hatayla kapandı")
    finally:
        active_connections.discard(websocket)
