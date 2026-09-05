"""river_learner.py testleri.

İki regresyon buraya kilitlenir:
  1. HalfSpaceTrees ham skoru olasılık değildir; kalibrasyonsuz kullanıldığında
     durağan veride bile ~45 puanlık sabit taban ekliyor ve eşik sürekli
     aşılıyordu.
  2. Öznitelik şeması değiştiğinde eski pickle yüklenmemeli.
"""

import pickle

import pytest

import river_learner
from river_learner import _CALIBRATION_MIN_SAMPLES, _FEATURE_VERSION, RiverLearner


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Gerçek backend/data/river_model_state.pkl dosyasına dokunulmasın."""
    monkeypatch.setattr(river_learner, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(river_learner, "_STATE_PATH", tmp_path / "river_state.pkl")
    return tmp_path


class TestCalibration:
    def test_returns_zero_during_warmup(self):
        learner = RiverLearner()
        for _ in range(_CALIBRATION_MIN_SAMPLES - 1):
            assert learner.score_and_learn("T-1", 0.5) == 0.0

    def test_score_stays_within_bounds(self):
        learner = RiverLearner()
        for i in range(_CALIBRATION_MIN_SAMPLES + 300):
            score = learner.score_and_learn("T-1", (i % 20) * 0.05)
            assert 0.0 <= score <= 100.0

    def test_stationary_signal_does_not_sit_at_high_score(self):
        """Sabit bir sinyal kalibrasyondan sonra yüksek skor almamalı.

        Kalibrasyonsuz sürümde bu ortalama ~45+ çıkıyor ve 50 eşiğini
        sürekli tetikliyordu.
        """
        learner = RiverLearner()
        for _ in range(_CALIBRATION_MIN_SAMPLES + 200):
            learner.score_and_learn("T-1", 0.5)

        scores = [learner.score_and_learn("T-1", 0.5) for _ in range(200)]
        mean_score = sum(scores) / len(scores)
        assert mean_score < 50.0

    def test_normal_negative_values_are_not_automatically_anomalous(self):
        """Telemetri [-1, 1] aralığına normalize edilmiştir.

        Öznitelik sınırları verilmezse HalfSpaceTrees tüm negatif değerleri
        'aralık dışı' sayıp yüksek skor veriyordu.
        """
        learner = RiverLearner()
        for _ in range(_CALIBRATION_MIN_SAMPLES + 200):
            learner.score_and_learn("T-1", -0.8)

        scores = [learner.score_and_learn("T-1", -0.8) for _ in range(100)]
        assert sum(scores) / len(scores) < 50.0

    def test_feature_limits_cover_normalised_telemetry_range(self):
        assert river_learner._FEATURE_LIMITS["v"] == (-1.0, 1.0)
        assert river_learner._FEATURE_LIMITS["c"] == (0.0, 1.0)


class TestStatePersistence:
    def test_stale_feature_version_is_ignored(self, isolated_state):
        """Eski şemayla eğitilmiş durum yüklenmemeli."""
        state_path = isolated_state / "river_state.pkl"
        with open(state_path, "wb") as f:
            pickle.dump(
                {
                    "feature_version": _FEATURE_VERSION - 1,
                    "model": "bozuk-model",
                    "n_samples_seen": 999_999,
                },
                f,
            )

        learner = RiverLearner()

        assert learner.get_model_stats()["n_samples_seen"] == 0

    def test_current_feature_version_is_loaded(self, isolated_state):
        learner = RiverLearner()
        for _ in range(10):
            learner.score_and_learn("T-1", 0.5)
        learner._save()

        reloaded = RiverLearner()

        assert reloaded.get_model_stats()["n_samples_seen"] == 10

    def test_corrupt_state_file_falls_back_to_fresh_model(self, isolated_state):
        (isolated_state / "river_state.pkl").write_bytes(b"bu bir pickle degil")

        learner = RiverLearner()

        assert learner.get_model_stats()["n_samples_seen"] == 0

    def test_reset_clears_state_and_file(self, isolated_state):
        learner = RiverLearner()
        for _ in range(10):
            learner.score_and_learn("T-1", 0.5)
        learner._save()
        assert (isolated_state / "river_state.pkl").is_file()

        learner.reset_model()

        assert learner.get_model_stats()["n_samples_seen"] == 0
        assert not (isolated_state / "river_state.pkl").is_file()
