"""rl_agent.py testleri.

Kalıcılık tarafı kritik: novelty tanımı değiştiğinde durum uzayının anlamı da
değişir. Sürüm koruması olmadan eski Q-tablo yanlış durumlara ödül atfediyor ve
eşik ayarı bozuluyordu.
"""

import pickle

import pytest

import rl_agent
from rl_agent import _ACTIONS, _STATE_VERSION, RLAgent


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Gerçek backend/data/rl_qtable.pkl dosyasına dokunulmasın."""
    monkeypatch.setattr(rl_agent, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(rl_agent, "_Q_PATH", tmp_path / "rl_qtable.pkl")
    return tmp_path / "rl_qtable.pkl"


class TestStateSpace:
    def test_state_buckets_cover_expected_ranges(self):
        agent = RLAgent()
        assert agent._state_key(0.0, 80.0, False) == (0, 2, 0)
        assert agent._state_key(25.0, 50.0, False) == (1, 1, 0)
        assert agent._state_key(99.0, 10.0, True) == (4, 0, 1)

    def test_scores_above_100_are_clamped(self):
        agent = RLAgent()
        assert agent._state_key(500.0, 80.0, False)[0] == 5

    def test_state_space_is_bounded(self):
        """6 skor x 3 batarya x 2 novelty = 36 olası durum."""
        agent = RLAgent()
        for score in range(0, 200, 3):
            for battery in range(0, 101, 7):
                for novelty in (True, False):
                    agent.select_action(float(score), float(battery), novelty)
        assert len(agent._q) <= 36

    def test_threshold_adjustment_returns_known_action(self):
        agent = RLAgent()
        adjustment, index = agent.get_threshold_adjustment(50.0, 75.0, False)
        assert adjustment in _ACTIONS
        assert _ACTIONS[index] == adjustment


class TestLearning:
    def test_reward_moves_q_value_toward_reward(self):
        agent = RLAgent(epsilon=0.0)
        agent.update_from_action(80.0, 75.0, False, 2, 10.0)
        state = agent._state_key(80.0, 75.0, False)
        assert agent._q[state][2] == pytest.approx(2.5)  # alpha=0.25

    def test_greedy_agent_picks_best_known_action(self):
        agent = RLAgent(epsilon=0.0)
        for _ in range(20):
            agent.update_from_action(80.0, 75.0, False, 2, 10.0)
            agent.update_from_action(80.0, 75.0, False, 0, -5.0)

        assert agent.select_action(80.0, 75.0, False) == 2

    def test_stats_track_totals(self):
        agent = RLAgent()
        agent.update_from_action(80.0, 75.0, False, 1, 10.0)
        agent.update_from_action(80.0, 75.0, False, 1, 5.0)

        stats = agent.get_rl_stats()
        assert stats["steps"] == 2
        assert stats["total_reward"] == pytest.approx(15.0)

    def test_earth_feedback_adjusts_exploration(self):
        agent = RLAgent(epsilon=0.15)

        agent.apply_earth_feedback(70.0)
        assert agent.get_rl_stats()["epsilon"] > 0.15

        for _ in range(50):
            agent.apply_earth_feedback(40.0)
        assert agent.get_rl_stats()["epsilon"] == pytest.approx(0.05)


class TestStatePersistence:
    def test_stale_state_version_is_ignored(self, isolated_state):
        with open(isolated_state, "wb") as f:
            pickle.dump(
                {
                    "state_version": _STATE_VERSION - 1,
                    "q": [{"k": [5, 2, 1], "v": [99.0, 99.0, 99.0]}],
                    "steps": 12345,
                },
                f,
            )

        agent = RLAgent()

        assert agent.get_rl_stats()["steps"] == 0
        assert agent.get_rl_stats()["q_table_size"] == 0

    def test_versionless_legacy_file_is_ignored(self, isolated_state):
        """Sürüm alanı olmayan eski dosyalar v1 sayılır ve reddedilir."""
        with open(isolated_state, "wb") as f:
            pickle.dump({"q": [{"k": [5, 2, 1], "v": [99.0, 0.0, 0.0]}], "steps": 500}, f)

        agent = RLAgent()

        assert agent.get_rl_stats()["steps"] == 0

    def test_current_version_round_trips(self, isolated_state):
        agent = RLAgent()
        for _ in range(5):
            agent.update_from_action(80.0, 75.0, False, 2, 10.0)
        agent._save()

        reloaded = RLAgent()

        assert reloaded.get_rl_stats()["steps"] == 5
        assert reloaded.get_rl_stats()["q_table_size"] == 1

    def test_corrupt_file_falls_back_to_fresh_table(self, isolated_state):
        isolated_state.write_bytes(b"bu bir pickle degil")

        agent = RLAgent()

        assert agent.get_rl_stats()["steps"] == 0

    def test_save_failure_is_logged_not_swallowed(self, monkeypatch, caplog):
        """Disk hatası sessizce yutulmamalı."""
        agent = RLAgent()
        monkeypatch.setattr(
            agent, "_save", lambda: (_ for _ in ()).throw(OSError("disk dolu"))
        )

        with caplog.at_level("ERROR"):
            for _ in range(100):  # _SAVE_EVERY
                agent.update_from_action(80.0, 75.0, False, 1, 1.0)

        assert "kaydedilemedi" in caplog.text
