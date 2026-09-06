"""Yazma yapan uçlar için basit paylaşılan token koruması.

Okuma uçları ve WebSocket akışı herkese açık kalır; durum değiştiren uçlar
(`POST`, `PATCH`) `SENTINEL_API_TOKEN` ile korunur. Anahtar tanımlı değilse bu
uçlar tamamen kapatılır — böylece açık sunucuda yanlışlıkla yazılabilir veya
Groq harcaması tetiklenebilir bir uç kalmaz.
"""

from __future__ import annotations

import hmac
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)


def require_api_token(x_api_token: str = Header(default="")) -> None:
    expected = (os.getenv("SENTINEL_API_TOKEN") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Yazma uçları kapalı: SENTINEL_API_TOKEN tanımlı değil. "
                "backend/.env dosyasına bir anahtar ekleyin."
            ),
        )
    if not hmac.compare_digest(x_api_token.strip(), expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik X-API-Token başlığı.",
        )
