"""Batarya bütçesi ve buna bağlı anomali eşiği / zlib seviyesi.

Batarya artık rastgele yürüyüş değil, yapılan işin sonucudur. Önceki sürümde
`tick_battery()` her turda `random.uniform(-2, 2)` uyguluyordu; iletilen paket
sayısı ölçülüyor ama bataryaya hiç yansıtılmıyordu. Bu yüzden projenin
anlattığı "enerji duyarlı eşik" döngüsünün yalnızca yarısı çalışıyordu: eşik
bataryaya bakıyor, batarya ise yaptığı işe bakmıyordu.

Kapanan döngü:

    çok paket ilet -> batarya düşer -> eşik yükselir -> daha az paket ilet
                                                              -> batarya toparlar

Radyo iletimi baskın maliyettir; sıkıştırma ise CPU enerjisini radyo enerjisi
karşılığında harcar (yüksek zlib seviyesi = daha çok CPU, daha az bayt).

Zaman hızlandırılmıştır: gerçek bir Mars solu ~24.66 saattir, panelde gündüz/
gece salınımının görülebilmesi için varsayılan olarak bir sol
`SENTINEL_SOL_TICKS` tick sürer (10 saniyelik tick ile ~20 dakika).
"""

from __future__ import annotations

import logging
import math
import os
import random
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int, minimum: int) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except ValueError:
        logger.warning("%s sayı değil; %d kullanılıyor.", name, default)
        return default


# Bir solun kaç tick sürdüğü (tick = energy_update_loop aralığı, 10 sn).
SOL_TICKS = _env_int("SENTINEL_SOL_TICKS", 120, 8)

# Tick başına yüzde puanı cinsinden enerji kalemleri.
_IDLE_DRAIN = 0.25  # bilgisayar, ısıtıcılar — her koşulda
_PROCESSING_DRAIN_PER_READING = 0.01  # uçta skorlama
_UPLINK_DRAIN_PER_PACKET = 0.12  # radyo — baskın kalem
_COMPRESSION_DRAIN_PER_LEVEL = 0.03  # zlib seviyesi başına CPU maliyeti
_SOLAR_PEAK = 3.0  # öğle vakti azami şarj

_CRITICAL_BATTERY = 15.0


class EnergyController:
    def __init__(self, battery_level: float = 75.0) -> None:
        self._battery_level = float(battery_level)
        self._cpu_load = 15.0
        self._packets_last_tick = 0
        self._tick_count = 0

        # Bir sonraki tick'te bataryadan düşülecek birikmiş iş
        self._pending_readings = 0
        self._pending_uplink_packets = 0
        self._pending_compression_levels = 0

        # Panel için son tick'in dökümü
        self._last_solar_input = 0.0
        self._last_drain = 0.0
        self._critical_warned = False

    # --- iş kaydı -------------------------------------------------------

    def record_processing_load(self, batch_size: int) -> None:
        """Uçta işlenen batch — CPU yükü ve işleme enerjisi."""
        self._packets_last_tick = batch_size
        self._pending_readings += batch_size
        base = min(100.0, batch_size * 6.0)
        noise = random.uniform(-5.0, 8.0)
        self._cpu_load = float(max(0.0, min(100.0, base + noise)))

    def record_uplink_energy(self, packet_count: int, zlib_level: int) -> None:
        """Gerçekten iletilen paketlerin radyo + sıkıştırma maliyeti."""
        if packet_count <= 0:
            return
        self._pending_uplink_packets += packet_count
        self._pending_compression_levels += int(zlib_level)

    # --- batarya --------------------------------------------------------

    def _solar_input(self) -> float:
        """Sol içindeki konuma göre panel girişi; gece 0."""
        phase = (self._tick_count % SOL_TICKS) / SOL_TICKS
        if phase >= 0.5:  # gece
            return 0.0
        # Gündüzün yarım sinüsü: şafak ve gün batımında 0, öğlen tepe
        return _SOLAR_PEAK * math.sin(math.pi * phase * 2.0)

    def tick_battery(self) -> None:
        self._tick_count += 1

        drain = (
            _IDLE_DRAIN
            + self._pending_readings * _PROCESSING_DRAIN_PER_READING
            + self._pending_uplink_packets * _UPLINK_DRAIN_PER_PACKET
            + self._pending_compression_levels * _COMPRESSION_DRAIN_PER_LEVEL
        )
        solar = self._solar_input()

        self._pending_readings = 0
        self._pending_uplink_packets = 0
        self._pending_compression_levels = 0

        self._last_solar_input = solar
        self._last_drain = drain
        self._battery_level = float(
            max(0.0, min(100.0, self._battery_level + solar - drain))
        )

        if self._battery_level <= _CRITICAL_BATTERY:
            if not self._critical_warned:
                logger.warning(
                    "Batarya kritik seviyede (%.1f%%); eşik yükseltilerek "
                    "iletim kısılıyor.",
                    self._battery_level,
                )
                self._critical_warned = True
        else:
            self._critical_warned = False

    # --- karar çıktıları ------------------------------------------------

    def get_threshold_and_zlib(self) -> Tuple[int, int]:
        """Batarya düştükçe eşik yükselir, sıkıştırma sertleşir.

        Radyo maliyeti CPU maliyetinden baskın olduğu için düşük bataryada
        daha agresif sıkıştırmak (daha çok CPU) toplamda kazançlıdır.
        """
        b = self._battery_level
        if b < 20:
            return 70, 9
        if b <= 50:
            return 60, 7
        return 50, 6

    def get_battery_level(self) -> float:
        return float(self._battery_level)

    def is_daylight(self) -> bool:
        return self._solar_input() > 0.0

    def get_energy_stats(self) -> Dict[str, Any]:
        th, zl = self.get_threshold_and_zlib()
        phase = (self._tick_count % SOL_TICKS) / SOL_TICKS
        return {
            "batarya_level": round(self._battery_level, 2),
            "cpu_load": round(self._cpu_load, 2),
            "aktif_esik": th,
            "zlib_level": zl,
            # Enerji dengesinin dökümü — bataryanın neden değiştiği görünür
            "solar_input": round(self._last_solar_input, 3),
            "drain": round(self._last_drain, 3),
            "net_change": round(self._last_solar_input - self._last_drain, 3),
            "is_daylight": self.is_daylight(),
            "sol_progress": round(phase, 3),
            "sol_ticks": SOL_TICKS,
        }
