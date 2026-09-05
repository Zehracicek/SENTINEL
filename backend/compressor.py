"""Delta encoding + zlib DEFLATE for uplink payload metrics (edge → DSN)."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class CompressResult:
    compressed: bytes
    serialized_bytes: int
    compressed_bytes: int


def readings_to_f64_payload(readings: Sequence[dict]) -> bytes:
    """Pack raw_value + anomaly_score per reading as little-endian float64."""
    parts: List[float] = []
    for r in readings:
        parts.append(float(r["raw_value"]))
        parts.append(float(r.get("anomaly_score", 0.0)))
    if not parts:
        return b""
    return struct.pack(f"<{len(parts)}d", *parts)


def delta_encode_f64_blob(blob: bytes) -> bytes:
    """First value unchanged; following values are successive differences."""
    n = len(blob) // 8
    if n == 0:
        return b""
    values = struct.unpack(f"<{n}d", blob)
    out: List[float] = [values[0]]
    for i in range(1, n):
        out.append(values[i] - values[i - 1])
    return struct.pack(f"<{n}d", *out)


def delta_decode_f64_blob(blob: bytes) -> bytes:
    """Inverse of delta_encode_f64_blob (for verification / tests)."""
    n = len(blob) // 8
    if n == 0:
        return b""
    deltas = struct.unpack(f"<{n}d", blob)
    restored: List[float] = [deltas[0]]
    for i in range(1, n):
        restored.append(restored[-1] + deltas[i])
    return struct.pack(f"<{n}d", *restored)


def deflate_compress(data: bytes, level: int = 6) -> bytes:
    return zlib.compress(data, level=level)


def compress_readings_delta_deflate(
    readings: Sequence[dict],
    *,
    zlib_level: int = 6,
) -> CompressResult:
    """
    Serialize readings, apply delta encoding on the float stream, then DEFLATE.
    Returns sizes for telemetry (serialized = pre-zlib binary size).
    """
    raw = readings_to_f64_payload(readings)
    if not raw:
        return CompressResult(compressed=b"", serialized_bytes=0, compressed_bytes=0)
    delta = delta_encode_f64_blob(raw)
    z = deflate_compress(delta, level=zlib_level)
    return CompressResult(compressed=z, serialized_bytes=len(raw), compressed_bytes=len(z))
