"""NASA Open API proxy — APOD ve Mars Rover Photos.

Anahtar yoksa NASA'nın resmi ücretsiz `DEMO_KEY` değeri kullanılır
(saatlik ~30 istek / IP). Sunumda sayfa boş kalmaz. Kişisel anahtar
https://api.nasa.gov adresinden ücretsiz alınır (saatlik ~1000).
"""

import os
import time
from typing import Any, Literal, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/nasa", tags=["NASA"])

NASA_BASE = "https://api.nasa.gov"
# NASA dokümantasyonunda yayımlanan demo anahtar — sır değildir.
_DEMO_KEY = "DEMO_KEY"
_CACHE_TTL_SEC = 15 * 60
_cache: dict[str, tuple[float, Any]] = {}


def _resolve_key() -> Tuple[str, str]:
    key = (os.getenv("NASA_API_KEY") or "").strip()
    if not key or key.upper() == _DEMO_KEY:
        return _DEMO_KEY, "demo"
    return key, "personal"


def _cache_get(key: str):
    hit = _cache.get(key)
    if not hit:
        return None
    ts, value = hit
    if time.monotonic() - ts > _CACHE_TTL_SEC:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> Any:
    _cache[key] = (time.monotonic(), value)
    return value


def _key_meta() -> dict:
    _, mode = _resolve_key()
    return {
        "key_mode": mode,
        "hourly_limit_hint": 30 if mode == "demo" else 1000,
    }


@router.get("/status")
async def nasa_status():
    meta = _key_meta()
    return {
        "ready": True,
        **meta,
        "note": (
            "Ücretsiz DEMO_KEY kullanılıyor (saatlik kota düşük). "
            "Kişisel anahtar: https://api.nasa.gov — backend/.env → NASA_API_KEY"
            if meta["key_mode"] == "demo"
            else "Kişisel NASA Open API anahtarı tanımlı."
        ),
    }


@router.get("/apod")
async def apod(
    date: Optional[str] = Query(
        None,
        description="YYYY-MM-DD (verilmezse bugün)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    cache_key = f"apod:{date or 'today'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    key, _mode = _resolve_key()
    params = {"api_key": key}
    if date:
        params["date"] = date
    url = f"{NASA_BASE}/planetary/apod"
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.get(url, params=params)
    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"NASA APOD yanıtı: {r.status_code}",
        )
    body = r.json()
    if isinstance(body, dict):
        body["_sentinel"] = _key_meta()
    return _cache_set(cache_key, body)


@router.get("/mars-photos/{rover}")
async def mars_photos(
    rover: Literal["curiosity", "opportunity", "spirit"],
    earth_date: Optional[str] = Query(
        None,
        description="YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    sol: Optional[int] = Query(None, ge=0, description="Mars günü (earth_date ile birlikte vermeyin)"),
    camera: Optional[str] = Query(None, max_length=32, description="Örn. fhaz, rhaz, mast"),
    page: int = Query(1, ge=1, le=100),
):
    if earth_date is None and sol is None:
        raise HTTPException(
            status_code=400,
            detail="earth_date veya sol parametrelerinden biri gerekli.",
        )
    if earth_date is not None and sol is not None:
        raise HTTPException(
            status_code=400,
            detail="earth_date ve sol birlikte kullanılamaz.",
        )
    key, _mode = _resolve_key()
    params: dict = {"api_key": key, "page": page}
    if earth_date:
        params["earth_date"] = earth_date
    else:
        params["sol"] = sol
    if camera:
        params["camera"] = camera
    url = f"{NASA_BASE}/mars-photos/api/v1/rovers/{rover}/photos"
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.get(url, params=params)
    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"NASA Mars Photos yanıtı: {r.status_code}",
        )
    return r.json()


def _from_images_library(items: list, rover: str, limit: int) -> list[dict]:
    """images-api.nasa.gov öğelerini mevcut galeri şekline çevirir."""
    photos: list[dict] = []
    for item in items:
        data = (item.get("data") or [{}])[0]
        links = item.get("links") or []
        preview = next(
            (ln.get("href") for ln in links if ln.get("href")),
            None,
        )
        if not preview:
            continue
        photos.append(
            {
                "id": data.get("nasa_id") or preview,
                "img_src": preview,
                "sol": None,
                "earth_date": (data.get("date_created") or "")[:10],
                "camera": {"name": (data.get("center") or "NASA").upper()},
                "rover": {"name": rover},
                "title": data.get("title") or "",
            }
        )
        if len(photos) >= limit:
            break
    return photos


@router.get("/mars-photos-recent/{rover}")
async def mars_photos_recent(
    rover: Literal["curiosity", "opportunity", "spirit"],
    limit: int = Query(12, ge=1, le=50, description="Toplanacak en fazla fotoğraf"),
):
    """Galeriyi NASA Image Library'den doldurur (anahtar gerekmez).

    Eski `mars-photos` uçları api.nasa.gov üzerinde 2026'da 404 dönüyor;
    images-api.nasa.gov ücretsiz ve anahtarsızdır.
    """
    cache_key = f"images:{rover}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    q = f"{rover} rover mars"
    url = "https://images-api.nasa.gov/search"
    async with httpx.AsyncClient(timeout=45.0) as client:
        r = await client.get(
            url,
            params={"q": q, "media_type": "image", "page_size": limit},
        )
    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"NASA Image Library yanıtı: {r.status_code}",
        )
    items = ((r.json() or {}).get("collection") or {}).get("items") or []
    photos = _from_images_library(items, rover, limit)
    payload = {
        "photos": photos,
        "meta": {
            **_key_meta(),
            "rover": rover,
            "count": len(photos),
            "source": "nasa_images_api",
            "start_sol": None,
            "end_sol": None,
        },
    }
    return _cache_set(cache_key, payload)
