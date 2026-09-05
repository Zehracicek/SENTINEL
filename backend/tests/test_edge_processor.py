"""edge_processor.py çekirdek karar mantığı testleri.

`process_batch` veritabanına dokunmaz — dict listesi alır, dict listesi döner.
Bu yüzden karar motoru, bant genişliği metrikleri ve RL ödül eşleştirmesi
gerçek Postgres olmadan test edilebilir.
"""

import uuid
from datetime import datetime, timezone

import pytest

from compressor import readings_to_f64_payload
from edge_processor import EdgeProcessor
from energy_controller import EnergyController


def make_reading(sensor_type="TEMP", channel_id="T-1", value=0.5, **extra):
    reading = {
        "id": uuid.uuid4(),
        "sensor_type": sensor_type,
        "raw_value": value,
        "unit": "°C",
        "location_lat": -4.5892,
        "location_lon": 137.4417,
        "sol": 1,
        "created_at": datetime.now(timezone.utc),
        "_chan_id": channel_id,
        "_chan_label": "Test Kanalı",
        "_idx": 0,
        "_is_labeled_anomaly": False,
        "_smoothed_error": None,
        "_prediction": None,
    }
    reading.update(extra)
    return reading


class TestThresholdDecision:
    """Tek dinamik eşik hem anomali etiketini hem iletim kararını belirler."""

    async def test_anomaly_and_uplink_use_the_same_threshold(self):
        processor = EdgeProcessor()
        batch = [make_reading(value=v) for v in (0.1, 0.2, 0.15)]

        processed, _events, _log = await processor.process_batch(batch)

        for reading in processed:
            # İki karar aynı koşuldan türediği için hiçbir zaman ayrışmamalı
            assert reading["is_anomaly"] == reading.get("_uplink_eligible", False)

    async def test_zscore_history_is_per_channel_not_sensor_type(self):
        """T-1 ve T-2 aynı TEMP tipini paylaşır; geçmiş karışmamalı."""
        processor = EdgeProcessor()
        for _ in range(20):
            await processor.process_batch(
                [
                    make_reading(sensor_type="TEMP", channel_id="T-1", value=0.5),
                    make_reading(sensor_type="TEMP", channel_id="T-2", value=10.0),
                ]
            )
        t1, _, _ = await processor.process_batch(
            [make_reading(sensor_type="TEMP", channel_id="T-1", value=0.5)]
        )
        assert t1[0]["anomaly_score"] < 15

    async def test_replay_index_is_persisted_on_db_row(self):
        processor = EdgeProcessor()
        batch = [make_reading(_idx=42)]
        processed, _, _ = await processor.process_batch(batch)
        assert processed[0]["replay_index"] == 42

    async def test_extreme_value_scores_higher_than_stable_value(self):
        processor = EdgeProcessor()
        # Kanal geçmişini sabit bir değerle doldur
        for _ in range(20):
            await processor.process_batch([make_reading(value=0.5)])

        stable, _, _ = await processor.process_batch([make_reading(value=0.5)])
        spike, _, _ = await processor.process_batch([make_reading(value=95.0)])

        assert spike[0]["anomaly_score"] > stable[0]["anomaly_score"]

    async def test_low_battery_raises_threshold(self):
        """Batarya düştükçe eşik yükselir; aynı skor artık anomali sayılmaz."""
        energy = EnergyController()

        energy._battery_level = 80.0
        assert energy.get_threshold_and_zlib()[0] == 50

        energy._battery_level = 40.0
        assert energy.get_threshold_and_zlib()[0] == 60

        energy._battery_level = 10.0
        assert energy.get_threshold_and_zlib()[0] == 70

    async def test_low_battery_uses_stronger_compression(self):
        energy = EnergyController()
        energy._battery_level = 80.0
        _, weak = energy.get_threshold_and_zlib()
        energy._battery_level = 10.0
        _, strong = energy.get_threshold_and_zlib()
        assert strong > weak


class TestBandwidthMetrics:
    """Tasarruf iddiası hiçbir zaman verinin gerçek hacmini aşmamalı.

    Önceki sürüm sabit "256 byte/paket" varsayımı yüzünden toplam veri
    hacminin ~11 katı tasarruf raporluyordu.
    """

    async def test_bytes_saved_never_exceeds_baseline_volume(self):
        processor = EdgeProcessor()
        batch = [make_reading(channel_id=f"T-{i}", value=i * 0.1) for i in range(12)]

        _processed, _events, log = await processor.process_batch(batch)

        assert log is not None
        assert log["bytes_saved"] <= log["baseline_bytes"]
        assert log["uplink_bytes"] <= log["baseline_bytes"]
        assert log["bytes_saved"] == log["baseline_bytes"] - log["uplink_bytes"]

    async def test_baseline_matches_actual_serialized_size(self):
        processor = EdgeProcessor()
        batch = [make_reading(channel_id=f"T-{i}") for i in range(12)]

        processed, _events, log = await processor.process_batch(batch)

        assert log["baseline_bytes"] == len(readings_to_f64_payload(processed))
        assert log["baseline_bytes"] == 12 * 16

    async def test_compression_ratio_is_byte_based_and_bounded(self):
        processor = EdgeProcessor()
        batch = [make_reading(channel_id=f"T-{i}") for i in range(12)]

        _processed, _events, log = await processor.process_batch(batch)

        assert 0.0 <= log["compression_ratio"] <= 1.0
        assert 0.0 <= log["packet_ratio"] <= 1.0

    async def test_stats_savings_percent_stays_in_range(self):
        processor = EdgeProcessor()
        for _ in range(5):
            batch = [make_reading(channel_id=f"T-{i}") for i in range(12)]
            processed, _events, _log = await processor.process_batch(batch)
            eligible = [r for r in processed if r.get("_uplink_eligible")]
            processor.record_uplink_batch(eligible)

        stats = processor.get_stats()
        assert 0.0 <= stats["bandwidth_saved_percent"] <= 100.0
        assert stats["total_bytes_saved"] <= stats["baseline_bytes"]


class TestNoveltyDetection:
    """Novelty, aynı kanalda görülen en yakın değere uzaklıktan türer."""

    async def test_first_reading_on_channel_is_not_novel(self):
        processor = EdgeProcessor()
        is_novel, similarity = processor._novelty_check("T-1", 0.5)
        assert is_novel is False
        assert similarity == 1.0

    async def test_repeated_value_is_highly_similar(self):
        processor = EdgeProcessor()
        processor._novelty_check("T-1", 0.5)
        is_novel, similarity = processor._novelty_check("T-1", 0.5)
        assert is_novel is False
        assert similarity == pytest.approx(1.0)

    async def test_distant_value_is_flagged_novel(self):
        processor = EdgeProcessor()
        processor._novelty_check("T-1", 0.0)
        is_novel, similarity = processor._novelty_check("T-1", 5.0)
        assert is_novel is True
        assert similarity < 0.3

    async def test_channels_keep_separate_history(self):
        """Bir kanaldaki değer, başka kanalı 'görülmüş' yapmamalı."""
        processor = EdgeProcessor()
        processor._novelty_check("T-1", 0.5)
        _is_novel, similarity = processor._novelty_check("P-10", 0.5)
        assert similarity == 1.0  # P-10 için ilk okuma


class TestRLRewardPairing:
    """Ödül, paketi kuyruğa alan kararın durumuna yazılmalı."""

    def test_reward_rises_for_high_score_anomaly(self):
        high = EdgeProcessor._uplink_reward(
            {"anomaly_score": 80.0, "is_anomaly": True, "is_novel": False}
        )
        assert high == pytest.approx(10.0)

    def test_reward_penalises_low_score_transmission(self):
        wasted = EdgeProcessor._uplink_reward(
            {"anomaly_score": 30.0, "is_anomaly": False, "is_novel": False}
        )
        assert wasted == pytest.approx(-5.0)

    def test_novelty_adds_bonus(self):
        without = EdgeProcessor._uplink_reward(
            {"anomaly_score": 80.0, "is_anomaly": True, "is_novel": False}
        )
        with_novelty = EdgeProcessor._uplink_reward(
            {"anomaly_score": 80.0, "is_anomaly": True, "is_novel": True}
        )
        assert with_novelty == pytest.approx(without + 5.0)

    def test_decision_memory_is_bounded(self):
        processor = EdgeProcessor()
        for i in range(6000):
            processor._remember_rl_decision(f"id-{i}", 50.0, 75.0, False, 1)
        assert len(processor._rl_decisions) <= 5000

    def test_reward_goes_to_the_decision_that_queued_the_packet(self):
        """Uplink drain batch'lerce sonra gelir; ödül en son duruma değil,
        paketi kuyruğa alan duruma yazılmalı."""
        processor = EdgeProcessor(rl_agent=_RecordingRL())
        old_id = uuid.uuid4()
        processor._remember_rl_decision(str(old_id), 91.0, 30.0, True, 2)
        # Araya başka kararlar girsin (durum değişti)
        for i in range(10):
            processor._remember_rl_decision(f"other-{i}", 10.0, 90.0, False, 0)

        processor.apply_rl_rewards_after_uplink(
            [{"id": old_id, "anomaly_score": 80.0, "is_anomaly": True}]
        )

        assert len(processor._rl.calls) == 1
        mean_score, battery, novelty, action_idx, _reward = processor._rl.calls[0]
        assert (mean_score, battery, novelty, action_idx) == (91.0, 30.0, True, 2)

    def test_reward_is_consumed_only_once(self):
        processor = EdgeProcessor(rl_agent=_RecordingRL())
        reading_id = uuid.uuid4()
        processor._remember_rl_decision(str(reading_id), 70.0, 50.0, False, 1)
        packet = {"id": reading_id, "anomaly_score": 80.0, "is_anomaly": True}

        processor.apply_rl_rewards_after_uplink([packet])
        processor.apply_rl_rewards_after_uplink([packet])

        assert len(processor._rl.calls) == 1

    def test_unmatched_reading_is_skipped_without_error(self):
        """Sunucu yeniden başladıysa eski paketin kararı bellekte yoktur."""
        processor = EdgeProcessor(rl_agent=_RecordingRL())

        processor.apply_rl_rewards_after_uplink(
            [{"id": uuid.uuid4(), "anomaly_score": 70.0, "is_anomaly": True}]
        )

        assert processor._rl.calls == []


class _RecordingRL:
    """update_from_action çağrılarını kaydeden sahte RL ajanı (disk kullanmaz)."""

    def __init__(self):
        self.calls = []

    def get_threshold_adjustment(self, anomaly_score, battery_level, novelty):
        return 0, 1

    def update_from_action(
        self, anomaly_score, battery_level, novelty, action_idx, reward
    ):
        self.calls.append((anomaly_score, battery_level, novelty, action_idx, reward))
