"""Yerel çalışma ayarları — süreç yeniden başlasa da kalır."""

from __future__ import annotations

import json
import os
from pathlib import Path

_STATE = Path(__file__).resolve().parent / "data" / "rover_thinking.json"


def groq_configured() -> bool:
    return bool((os.getenv("GROQ_API_KEY") or "").strip())


def load_thinking_enabled() -> bool:
    raw = (os.getenv("SENTINEL_ROVER_THINKING_ENABLED") or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    if _STATE.exists():
        try:
            return bool(json.loads(_STATE.read_text(encoding="utf-8")).get("enabled"))
        except (OSError, ValueError, TypeError):
            pass
    return groq_configured()


def save_thinking_enabled(enabled: bool) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(
        json.dumps({"enabled": bool(enabled)}, ensure_ascii=False),
        encoding="utf-8",
    )
