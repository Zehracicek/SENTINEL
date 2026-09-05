"""compressor.py testleri.

Bu dosya, `delta_decode_f64_blob` docstring'inin bahsettiği ama daha önce hiç
yazılmamış doğrulamayı içerir. Round-trip'in bit düzeyinde birebir OLMADIĞI
(kümülatif float toplamı kaynaklı) burada açıkça belgelenir.
"""

import struct

import pytest

from compressor import (
    compress_readings_delta_deflate,
    delta_decode_f64_blob,
    delta_encode_f64_blob,
    readings_to_f64_payload,
)

BYTES_PER_READING = 16  # raw_value + anomaly_score, ikisi de float64


def _readings(values):
    return [{"raw_value": v, "anomaly_score": 50.0} for v in values]


def test_serialized_size_is_16_bytes_per_reading():
    """Paket boyutu varsayımı: bir okuma 2 x float64 = 16 byte.

    Bant genişliği metriği bu sabite dayanıyor; değişirse metrik bozulur.
    """
    blob = readings_to_f64_payload(_readings([0.1, 0.2, 0.3]))
    assert len(blob) == 3 * BYTES_PER_READING


def test_empty_input_produces_empty_output():
    assert readings_to_f64_payload([]) == b""
    assert delta_encode_f64_blob(b"") == b""
    assert delta_decode_f64_blob(b"") == b""
    result = compress_readings_delta_deflate([])
    assert result.serialized_bytes == 0
    assert result.compressed_bytes == 0
    assert result.compressed == b""


def test_delta_encoding_first_value_unchanged_rest_are_differences():
    blob = struct.pack("<3d", 10.0, 12.5, 12.0)
    encoded = struct.unpack("<3d", delta_encode_f64_blob(blob))
    assert encoded[0] == pytest.approx(10.0)
    assert encoded[1] == pytest.approx(2.5)
    assert encoded[2] == pytest.approx(-0.5)


def test_delta_round_trip_is_numerically_close_but_not_bit_exact():
    """Delta kodlaması kümülatif toplamla geri açıldığı için float hatası birikir.

    Sıkıştırma bu nedenle bit düzeyinde kayıplıdır. Tolerans içinde doğru
    olması yeterlidir; birebir eşitlik BEKLENMEZ.
    """
    values = [0.8155058142739824, 0.9935055767330221, -0.9991325248947283, 0.5, -0.25]
    blob = readings_to_f64_payload(_readings(values))

    restored = delta_decode_f64_blob(delta_encode_f64_blob(blob))

    assert len(restored) == len(blob)
    original = struct.unpack(f"<{len(blob) // 8}d", blob)
    back = struct.unpack(f"<{len(restored) // 8}d", restored)
    for a, b in zip(original, back, strict=True):
        assert a == pytest.approx(b, abs=1e-12)


def test_compression_reduces_size_for_repetitive_telemetry():
    """Ardışık benzer değerlerde delta + DEFLATE hacmi küçültmeli."""
    values = [0.99 + i * 1e-6 for i in range(64)]
    result = compress_readings_delta_deflate(_readings(values), zlib_level=6)

    assert result.serialized_bytes == 64 * BYTES_PER_READING
    assert result.compressed_bytes < result.serialized_bytes


def test_higher_zlib_level_is_not_larger():
    values = [0.5 + (i % 7) * 0.01 for i in range(128)]
    low = compress_readings_delta_deflate(_readings(values), zlib_level=1)
    high = compress_readings_delta_deflate(_readings(values), zlib_level=9)
    assert high.compressed_bytes <= low.compressed_bytes
