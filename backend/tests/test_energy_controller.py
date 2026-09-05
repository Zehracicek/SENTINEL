"""energy_controller.py testleri.

Kilitlenen davranış: batarya yapılan işin sonucu olmalı. Önceki sürüm
`random.uniform(-2, 2)` uyguluyor, iletilen paket sayısını hiç dikkate
almıyordu — yani "enerji duyarlı eşik" döngüsü açıktı.
"""

import energy_controller
from energy_controller import SOL_TICKS, EnergyController


def _run_ticks(controller, count, *, uplink_packets=0, zlib_level=6, readings=0):
    for _ in range(count):
        if readings:
            controller.record_processing_load(readings)
        if uplink_packets:
            controller.record_uplink_energy(uplink_packets, zlib_level)
        controller.tick_battery()


class TestWorkloadDrivesBattery:
    def test_transmitting_drains_more_than_staying_idle(self):
        idle = EnergyController(battery_level=90.0)
        busy = EnergyController(battery_level=90.0)

        _run_ticks(idle, 30, readings=12)
        _run_ticks(busy, 30, readings=12, uplink_packets=12)

        assert busy.get_battery_level() < idle.get_battery_level()

    def test_more_packets_drain_more(self):
        light = EnergyController(battery_level=90.0)
        heavy = EnergyController(battery_level=90.0)

        _run_ticks(light, 20, uplink_packets=2)
        _run_ticks(heavy, 20, uplink_packets=12)

        assert heavy.get_battery_level() < light.get_battery_level()

    def test_stronger_compression_costs_more_cpu_energy(self):
        weak = EnergyController(battery_level=90.0)
        strong = EnergyController(battery_level=90.0)

        _run_ticks(weak, 20, uplink_packets=5, zlib_level=1)
        _run_ticks(strong, 20, uplink_packets=5, zlib_level=9)

        assert strong.get_battery_level() < weak.get_battery_level()

    def test_battery_is_deterministic_for_identical_workload(self):
        """Rastgele yürüyüş kaldırıldı; aynı iş aynı sonucu vermeli."""
        first = EnergyController(battery_level=80.0)
        second = EnergyController(battery_level=80.0)

        _run_ticks(first, 25, uplink_packets=4)
        _run_ticks(second, 25, uplink_packets=4)

        assert first.get_battery_level() == second.get_battery_level()

    def test_work_is_consumed_once(self):
        """Birikmiş iş bir tick'te düşülüp sıfırlanmalı."""
        controller = EnergyController(battery_level=90.0)
        controller.record_uplink_energy(12, 6)
        controller.tick_battery()
        after_first = controller.get_battery_level()

        controller.tick_battery()  # yeni iş yok

        second_drop = after_first - controller.get_battery_level()
        assert second_drop < 0.5  # yalnızca idle + güneş etkisi


class TestFeedbackLoopClosesTheLoop:
    def test_heavy_transmission_eventually_raises_threshold(self):
        """Döngünün özü: çok iletim -> batarya düşer -> eşik yükselir."""
        controller = EnergyController(battery_level=60.0)
        assert controller.get_threshold_and_zlib()[0] == 50

        # Gece boyunca yoğun iletim (güneş yok)
        controller._tick_count = int(SOL_TICKS * 0.5)
        _run_ticks(controller, 40, readings=12, uplink_packets=12)

        assert controller.get_battery_level() < 50
        assert controller.get_threshold_and_zlib()[0] > 50

    def test_battery_recovers_in_daylight_when_idle(self):
        controller = EnergyController(battery_level=40.0)
        controller._tick_count = 0  # şafak

        _run_ticks(controller, 20)

        assert controller.get_battery_level() > 40.0


class TestSolarCycle:
    def test_no_solar_input_at_night(self):
        controller = EnergyController()
        controller._tick_count = int(SOL_TICKS * 0.75)
        assert controller._solar_input() == 0.0
        assert controller.is_daylight() is False

    def test_solar_peaks_around_midday(self):
        controller = EnergyController()
        controller._tick_count = int(SOL_TICKS * 0.25)
        midday = controller._solar_input()

        controller._tick_count = int(SOL_TICKS * 0.05)
        dawn = controller._solar_input()

        assert midday > dawn > 0.0
        assert controller._tick_count is not None

    def test_sol_progress_wraps(self):
        controller = EnergyController()
        _run_ticks(controller, SOL_TICKS * 2)
        assert 0.0 <= controller.get_energy_stats()["sol_progress"] < 1.0


class TestBounds:
    def test_battery_bottoms_out_at_zero_during_a_long_night(self):
        controller = EnergyController(battery_level=5.0)
        controller._tick_count = int(SOL_TICKS * 0.5)  # gecenin başı

        # Gece süresince kal (güneş girişi yok), tükenişi izle
        _run_ticks(controller, int(SOL_TICKS * 0.4), readings=12, uplink_packets=12)

        assert controller.get_battery_level() == 0.0

    def test_battery_never_goes_negative_across_many_sols(self):
        controller = EnergyController(battery_level=10.0)

        for _ in range(SOL_TICKS * 4):
            controller.record_processing_load(12)
            controller.record_uplink_energy(12, 9)
            controller.tick_battery()
            assert controller.get_battery_level() >= 0.0

    def test_battery_never_exceeds_hundred(self):
        controller = EnergyController(battery_level=99.0)
        controller._tick_count = 0

        _run_ticks(controller, SOL_TICKS * 3)

        assert controller.get_battery_level() <= 100.0

    def test_cpu_load_stays_in_range(self):
        controller = EnergyController()
        for size in (0, 1, 12, 500):
            controller.record_processing_load(size)
            assert 0.0 <= controller.get_energy_stats()["cpu_load"] <= 100.0

    def test_critical_battery_is_logged_once(self, caplog):
        controller = EnergyController(battery_level=16.0)
        controller._tick_count = int(SOL_TICKS * 0.5)  # gece

        with caplog.at_level("WARNING"):
            _run_ticks(controller, 10, uplink_packets=12)

        assert caplog.text.count("Batarya kritik") == 1


class TestConfiguration:
    def test_sol_length_is_configurable(self, monkeypatch):
        monkeypatch.setenv("SENTINEL_SOL_TICKS", "48")
        assert energy_controller._env_int("SENTINEL_SOL_TICKS", 120, 8) == 48

    def test_invalid_sol_length_falls_back(self, monkeypatch, caplog):
        monkeypatch.setenv("SENTINEL_SOL_TICKS", "abc")
        with caplog.at_level("WARNING"):
            value = energy_controller._env_int("SENTINEL_SOL_TICKS", 120, 8)
        assert value == 120

    def test_sol_length_has_a_floor(self, monkeypatch):
        monkeypatch.setenv("SENTINEL_SOL_TICKS", "1")
        assert energy_controller._env_int("SENTINEL_SOL_TICKS", 120, 8) == 8
