"""Groq (Llama) ile rover anomali düşünce metni.

Maliyet kontrolü burada yaşar. Bu modül anomali başına çağrılır ve anomali
sayısı veriye göre değişir; hiçbir sınır olmadan yüksek anomali oranlı bir
dönem doğrudan faturaya dönüşür. Bu yüzden:

  * iki kademeli kayan pencere sınırı (dakika ve saat) — üst sınır aşılırsa
    çağrı yapılmaz, fallback döner;
  * geçici hatalarda (429 / 5xx / ağ) sınırlı sayıda yeniden deneme,
    `Retry-After` başlığına saygı duyarak;
  * kalıcı hatalarda (401 gibi) yeniden deneme yok, net log;
  * her sonuç sayaçlara işlenir, `/health` üzerinden görünür.

GROQ_API_KEY tanımlı değilse hiç ağ çağrısı yapılmaz.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from collections import deque
from typing import Any, Deque, Dict, List

import httpx

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
# llama-3.3-70b-versatile Ağustos 2026'da kapatıldı; ücretsiz katmanda 404 verir.
MODEL_ID = (os.environ.get("GROQ_MODEL") or "openai/gpt-oss-20b").strip()

_REQUEST_TIMEOUT = 25.0
_MAX_ATTEMPTS = 3
_BACKOFF_BASE = 0.5
_MAX_RETRY_AFTER = 10.0


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        logger.warning("%s sayı değil (%r); %d kullanılıyor.", name, raw, default)
        return default


class _SlidingWindowLimit:
    """Belirli bir pencerede izin verilen azami çağrı sayısı."""

    def __init__(self, window_seconds: float, max_calls: int, label: str) -> None:
        self._window = window_seconds
        self._max_calls = max_calls
        self._label = label
        self._stamps: Deque[float] = deque()

    def _prune(self, now: float) -> None:
        cutoff = now - self._window
        while self._stamps and self._stamps[0] < cutoff:
            self._stamps.popleft()

    def allows(self, now: float) -> bool:
        if self._max_calls <= 0:
            return False
        self._prune(now)
        return len(self._stamps) < self._max_calls

    def record(self, now: float) -> None:
        self._stamps.append(now)

    @property
    def label(self) -> str:
        return self._label

    @property
    def used(self) -> int:
        self._prune(time.monotonic())
        return len(self._stamps)

    @property
    def limit(self) -> int:
        return self._max_calls


class _CostGuard:
    """Groq harcamasının üst sınırı ve kullanım sayaçları."""

    def __init__(self) -> None:
        self._limits = [
            _SlidingWindowLimit(
                60.0, _env_int("ROVER_THINK_MAX_CALLS_PER_MIN", 6), "dakika"
            ),
            _SlidingWindowLimit(
                3600.0, _env_int("ROVER_THINK_MAX_CALLS_PER_HOUR", 120), "saat"
            ),
        ]
        self._lock = asyncio.Lock()
        self.attempts = 0
        self.completed = 0
        self.rate_limited = 0
        self.failed = 0
        self.retried = 0

    async def try_acquire(self) -> bool:
        """Kota varsa tüketip True döner; yoksa çağrı yapılmamalı."""
        async with self._lock:
            now = time.monotonic()
            for limit in self._limits:
                if not limit.allows(now):
                    self.rate_limited += 1
                    logger.warning(
                        "Groq çağrısı atlandı: %s başına %d çağrı sınırına ulaşıldı "
                        "(ROVER_THINK_MAX_CALLS_PER_%s ile ayarlanır).",
                        limit.label,
                        limit.limit,
                        "MIN" if limit.label == "dakika" else "HOUR",
                    )
                    return False
            for limit in self._limits:
                limit.record(now)
            return True

    def usage(self) -> Dict[str, Any]:
        return {
            "attempts": self.attempts,
            "completed": self.completed,
            "failed": self.failed,
            "rate_limited": self.rate_limited,
            "retried": self.retried,
            "per_minute_used": self._limits[0].used,
            "per_minute_limit": self._limits[0].limit,
            "per_hour_used": self._limits[1].used,
            "per_hour_limit": self._limits[1].limit,
        }


_guard = _CostGuard()
_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()


async def _get_client() -> httpx.AsyncClient:
    """Paylaşımlı istemci — her çağrıda yeni bağlantı havuzu kurulmasın."""
    global _client
    if _client is None or _client.is_closed:
        async with _client_lock:
            if _client is None or _client.is_closed:
                _client = httpx.AsyncClient(
                    timeout=httpx.Timeout(_REQUEST_TIMEOUT),
                    limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
                )
    return _client


async def aclose() -> None:
    """Uygulama kapanışında çağrılır."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def get_usage_stats() -> Dict[str, Any]:
    """Groq kullanımı — /health üzerinden izlenir."""
    stats = _guard.usage()
    stats["enabled"] = bool((os.environ.get("GROQ_API_KEY") or "").strip())
    stats["model"] = MODEL_ID
    return stats


_SYSTEM_PROMPT = (
    "Sen SENTİNEL'sin — Mars yüzeyinde çalışan otonom bir rover yapay zekasısın. "
    "Görevin: sensör verilerini analiz edip bilimsel karar vermek. Düşünce sürecini "
    "adım adım, kısa ve teknik olarak Türkçe açıkla. Sonunda net bir karar ver: "
    "TX (ilet) veya DROP (atla)."
)


def _fallback_decision(context: Dict[str, Any]) -> str:
    if context.get("uplink_eligible"):
        return "TX"
    return "DROP"


def _fallback(ctx: Dict[str, Any], model: str, thinking: str) -> Dict[str, Any]:
    return {
        "thinking": thinking,
        "steps": [],
        "decision": _fallback_decision(ctx),
        "duration_ms": 0,
        "model": model,
    }


def _parse_decision_from_text(text: str, context: Dict[str, Any]) -> str:
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    if not lines:
        return _fallback_decision(context)
    last = lines[-1].upper()
    if re.search(r"\bDROP\b", last) or "ATLA" in last:
        return "DROP"
    if re.search(r"\bTX\b", last) or "İLET" in last or "ILET" in last:
        return "TX"
    return _fallback_decision(context)


def _build_user_prompt(ctx: Dict[str, Any]) -> str:
    is_novel = bool(ctx.get("is_novel"))
    novel_line = "EVET — yeni imza!" if is_novel else "HAYIR"
    return (
        f"Kanal: {ctx.get('channel_id', '?')} ({ctx.get('sensor_type', '?')})\n"
        f"Ham değer: {float(ctx.get('raw_value', 0)):.4f}\n"
        f"Anomali skoru: {float(ctx.get('anomaly_score', 0)):.1f}/100\n"
        f"River skoru: {float(ctx.get('river_score', 0)):.1f}/100\n"
        f"LSTM skoru: {float(ctx.get('lstm_score', 0)):.1f}/100\n"
        f"Yenilik tespiti: {novel_line}\n"
        f"Yenilik benzerliği: {float(ctx.get('novelty_similarity', 0)):.2f}\n"
        f"Enerji seviyesi: %{int(ctx.get('energy_level', 0))}\n"
        f"RL önerisi: {ctx.get('rl_suggestion', '—')}\n"
        f"Bilimsel öncelik: {int(ctx.get('scientific_priority', 0))}/10\n"
        f"Anomali tipi: {ctx.get('anomaly_type', '—')}\n\n"
        "Adım adım düşün ve kararını gerekçeli ver."
    )


def _retry_delay(attempt: int, response: httpx.Response | None) -> float:
    if response is not None:
        header = response.headers.get("Retry-After")
        if header:
            try:
                return min(_MAX_RETRY_AFTER, max(0.0, float(header)))
            except ValueError:
                pass
    return _BACKOFF_BASE * (2**attempt)


async def think(context: dict) -> dict:
    """anomaly_score >= 50 için çağrılmalı.

    API anahtarı yoksa, kota bittiyse veya çağrı başarısızsa fallback döner —
    her durumda uplink kararı bu fonksiyondan bağımsız olarak zaten alınmıştır.
    """
    ctx = dict(context)
    if float(ctx.get("anomaly_score") or 0) < 50:
        return _fallback(ctx, "skipped", "")

    api_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not api_key:
        return _fallback(ctx, "fallback", "AI thinking devre dışı")

    if not await _guard.try_acquire():
        return _fallback(ctx, "rate_limited", "AI thinking kotası doldu")

    body = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(ctx)},
        ],
        "max_tokens": 500,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    client = await _get_client()
    t0 = time.perf_counter()

    for attempt in range(_MAX_ATTEMPTS):
        _guard.attempts += 1
        try:
            resp = await client.post(GROQ_CHAT_URL, json=body, headers=headers)

            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = _retry_delay(attempt, resp)
                    _guard.retried += 1
                    logger.warning(
                        "Groq %d döndü; %.1f sn sonra yeniden denenecek (%d/%d).",
                        resp.status_code,
                        delay,
                        attempt + 1,
                        _MAX_ATTEMPTS - 1,
                    )
                    await asyncio.sleep(delay)
                    continue
                _guard.failed += 1
                logger.error(
                    "Groq %d döndü ve yeniden denemeler tükendi.", resp.status_code
                )
                return _fallback(ctx, "fallback", "AI thinking devre dışı")

            if resp.status_code >= 400:
                # 401/403/404 gibi kalıcı hatalar — tekrar denemek boşuna
                _guard.failed += 1
                logger.error(
                    "Groq isteği kalıcı hatayla reddedildi (%d): %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return _fallback(ctx, "fallback", "AI thinking devre dışı")

            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                _guard.failed += 1
                logger.error("Groq yanıtı boş 'choices' içeriyor.")
                return _fallback(ctx, "fallback", "AI thinking devre dışı")

            content = str((choices[0].get("message") or {}).get("content") or "").strip()
            steps: List[str] = content.split("\n")
            _guard.completed += 1
            return {
                "thinking": content,
                "steps": steps,
                "decision": _parse_decision_from_text(content, ctx),
                "duration_ms": int((time.perf_counter() - t0) * 1000),
                "model": MODEL_ID,
            }

        except (httpx.TimeoutException, httpx.TransportError) as exc:
            if attempt < _MAX_ATTEMPTS - 1:
                delay = _retry_delay(attempt, None)
                _guard.retried += 1
                logger.warning(
                    "Groq bağlantı hatası (%s); %.1f sn sonra yeniden denenecek.",
                    type(exc).__name__,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
            _guard.failed += 1
            logger.error("Groq bağlantısı kurulamadı: %s", exc)
            return _fallback(ctx, "fallback", "AI thinking devre dışı")

        except Exception:
            # Beklenmeyen hata: sessiz kalmasın, ama akışı durdurmasın.
            _guard.failed += 1
            logger.exception("Groq çağrısı beklenmeyen bir hatayla başarısız oldu")
            return _fallback(ctx, "fallback", "AI thinking devre dışı")

    _guard.failed += 1
    return _fallback(ctx, "fallback", "AI thinking devre dışı")
