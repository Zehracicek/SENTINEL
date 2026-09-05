"""Kanal kimliğini süreçler arası kararlı bir sayıya çevirir.

Daha önce hem River özniteliği hem novelty vektörü `hash(channel_id) % 1000`
kullanıyordu. Python'un str hash'i PYTHONHASHSEED ile her süreçte yeniden
rastgeleleştiği için `river_model_state.pkl` ve `rl_qtable.pkl` dosyalarına
kaydedilen öğrenme, sunucu yeniden başladığında farklı bir öznitelik uzayına
denk düşüyor ve geçersizleşiyordu.

Bilinen MSL kanalları sabit sıralarına göre eşit aralıklı değer alır; bilinmeyen
kanallar için CRC32 kullanılır (deterministik ve platformdan bağımsız).
"""

from __future__ import annotations

import zlib

# simulator.MSL_CHANNELS ile aynı sıra; buradaki sıra kalıcı model durumunun
# parçasıdır, mevcut kanalların sırasını değiştirmeyin (sona ekleyin).
KNOWN_CHANNELS: tuple[str, ...] = (
    "T-1",
    "T-2",
    "P-10",
    "P-14",
    "M-6",
    "M-7",
    "C-1",
    "C-2",
    "D-14",
    "D-15",
    "D-16",
    "F-7",
)

_INDEX = {cid: i for i, cid in enumerate(KNOWN_CHANNELS)}


def channel_code(channel_id: str) -> float:
    """Kanal kimliği -> [0, 1) aralığında kararlı bir değer."""
    idx = _INDEX.get(channel_id)
    if idx is not None:
        return idx / len(KNOWN_CHANNELS)
    return (zlib.crc32(channel_id.encode("utf-8")) % 1000) / 1000.0
