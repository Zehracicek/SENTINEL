"""Orbiter Edge 2: 30 sn pencere, ikincil filtre, relay istatistikleri."""

from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OrbiterPacket:
    reading_id: str
    sol: int
    anomaly_score: float
    sensor_type: str


@dataclass
class OrbiterProcessor:
    window_seconds: float = 30.0
    _buffer: List[OrbiterPacket] = field(default_factory=list)
    _window_start: float = field(default_factory=time.monotonic)
    _last_pass_id: str = ""
    _total_received: int = 0
    _total_forwarded: int = 0
    _total_dropped_secondary: int = 0
    _latency_samples: List[float] = field(default_factory=list)

    def _new_pass_id(self) -> str:
        self._last_pass_id = f"PASS-{uuid.uuid4().hex[:12].upper()}"
        return self._last_pass_id

    def ingest_forwarded(self, packets: List[OrbiterPacket]) -> None:
        # Pencere sonu ve kalıcı log yalnızca tick_flush_if_due() ile yapılır; aksi halde
        # _flush_window çıktısı yok sayılıyordu ve orbiter_relay_log boş kalıyordu.
        for p in packets:
            self._buffer.append(p)
            self._total_forwarded += 1
            self._latency_samples.append(random.uniform(180.0, 950.0))
            if len(self._latency_samples) > 200:
                self._latency_samples = self._latency_samples[-200:]

    def note_received(self, n: int) -> None:
        self._total_received += n

    def note_secondary_drop(self, n: int) -> None:
        self._total_dropped_secondary += n

    def _flush_window(self) -> Optional[Dict[str, Any]]:
        if not self._buffer:
            self._buffer.clear()
            return None
        pass_id = self._new_pass_id()
        n = len(self._buffer)
        self._buffer.clear()
        avg_lat = (
            sum(self._latency_samples[-n:]) / max(1, min(n, len(self._latency_samples)))
            if self._latency_samples
            else 0.0
        )
        return {
            "batch_id": str(uuid.uuid4()),
            "packets_received": n,
            "packets_forwarded": n,
            "relay_latency_ms": round(avg_lat, 2),
            "pass_id": pass_id,
        }

    def tick_flush_if_due(self) -> Optional[Dict[str, Any]]:
        now = time.monotonic()
        if now - self._window_start >= self.window_seconds and self._buffer:
            meta = self._flush_window()
            self._window_start = now
            return meta
        return None

    def get_ws_stats(self) -> Dict[str, Any]:
        recv = max(1, self._total_received)
        drop_r = self._total_dropped_secondary / recv
        avg_lat = (
            sum(self._latency_samples) / len(self._latency_samples)
            if self._latency_samples
            else 0.0
        )
        now = time.monotonic()
        elapsed = now - self._window_start
        remaining = max(0.0, self.window_seconds - elapsed)
        return {
            "packets_received": self._total_received,
            "packets_forwarded": self._total_forwarded,
            "packets_dropped_secondary": self._total_dropped_secondary,
            "drop_rate": round(min(1.0, drop_r), 4),
            "avg_relay_latency_ms": round(avg_lat, 2),
            "last_pass_id": self._last_pass_id,
            "window_seconds": self.window_seconds,
            "buffer_pending": len(self._buffer),
            "window_elapsed_sec": round(elapsed, 2),
            "window_remaining_sec": round(remaining, 2),
        }
