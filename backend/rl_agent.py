"""Epsilon-greedy Q-tablo ile iletim eşiği ince ayarı (.h5 yok)."""

from __future__ import annotations

import logging
import pickle
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent / "data"
_Q_PATH = _DATA_DIR / "rl_qtable.pkl"
_SAVE_EVERY = 100
_ACTIONS = (-5, 0, 5)  # eşik delta

# Durum uzayının anlamı değiştiğinde artırın. Q değerleri (skor kovası,
# batarya kovası, novelty) üçlüsüne bağlıdır; bu üçlünün tanımı değişirse eski
# tablo yanlış durumlara ödül atfeder ve eşik saçmalar.
# v2: novelty artık kosinüs benzerliği değil, kanal içi en yakın komşu
#     uzaklığından türetiliyor — aynı bayrak farklı bir olayı temsil ediyor.
_STATE_VERSION = 2


class RLAgent:
    def __init__(self, epsilon: float = 0.15) -> None:
        self._epsilon = epsilon
        self._q: Dict[Tuple[int, int, int], List[float]] = {}
        self._total_reward = 0.0
        self._steps = 0
        self._load_if_exists()

    def _state_key(
        self, anomaly_score: float, battery_level: float, novelty: bool
    ) -> Tuple[int, int, int]:
        sb = min(5, int(anomaly_score // 20))
        eb = 0 if battery_level < 33 else (1 if battery_level < 66 else 2)
        nv = 1 if novelty else 0
        return (sb, eb, nv)

    def _load_if_exists(self) -> None:
        if not _Q_PATH.is_file():
            return
        try:
            with open(_Q_PATH, "rb") as f:
                data = pickle.load(f)
        except Exception:
            logger.warning(
                "%s okunamadı; Q-tablo sıfırdan başlatılıyor.", _Q_PATH.name
            )
            return

        if not isinstance(data, dict):
            logger.warning("%s beklenmeyen biçimde; yok sayılıyor.", _Q_PATH.name)
            return

        saved_version = int(data.get("state_version", 1))
        if saved_version != _STATE_VERSION:
            logger.warning(
                "%s durum sürümü %d, beklenen %d — eski Q-tablo yok sayılıyor "
                "ve ajan sıfırdan öğrenmeye başlıyor.",
                _Q_PATH.name,
                saved_version,
                _STATE_VERSION,
            )
            return

        try:
            qraw = data.get("q", [])
            if isinstance(qraw, list):
                self._q = {
                    tuple(x["k"]): x["v"] for x in qraw if isinstance(x, dict)
                }
            self._epsilon = float(data.get("epsilon", self._epsilon))
            self._total_reward = float(data.get("total_reward", 0))
            self._steps = int(data.get("steps", 0))
        except (KeyError, TypeError, ValueError):
            logger.warning(
                "%s içeriği ayrıştırılamadı; Q-tablo sıfırlanıyor.", _Q_PATH.name
            )
            self._q = {}
            self._total_reward = 0.0
            self._steps = 0

    def _save(self) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        q_list = [{"k": list(k), "v": v} for k, v in self._q.items()]
        payload = {
            "state_version": _STATE_VERSION,
            "q": q_list,
            "epsilon": self._epsilon,
            "total_reward": self._total_reward,
            "steps": self._steps,
        }
        with open(_Q_PATH, "wb") as f:
            pickle.dump(payload, f)

    def select_action(self, anomaly_score: float, battery_level: float, novelty: bool) -> int:
        s = self._state_key(anomaly_score, battery_level, novelty)
        if s not in self._q:
            self._q[s] = [0.0, 0.0, 0.0]
        if random.random() < self._epsilon:
            return random.randrange(3)
        return int(max(range(3), key=lambda i: self._q[s][i]))

    def get_threshold_adjustment(
        self, anomaly_score: float, battery_level: float, novelty: bool
    ) -> Tuple[int, int]:
        ai = self.select_action(anomaly_score, battery_level, novelty)
        return _ACTIONS[ai], ai

    def update_from_action(
        self,
        anomaly_score: float,
        battery_level: float,
        novelty: bool,
        action_index: int,
        reward: float,
    ) -> None:
        s = self._state_key(anomaly_score, battery_level, novelty)
        if s not in self._q:
            self._q[s] = [0.0, 0.0, 0.0]
        alpha = 0.25
        self._q[s][action_index] = (1 - alpha) * self._q[s][action_index] + alpha * reward
        self._total_reward += reward
        self._steps += 1
        if self._steps % _SAVE_EVERY == 0:
            try:
                self._save()
            except Exception:
                # Sessiz kalırsa disk/izin sorunu yüzünden öğrenilen her şey
                # fark edilmeden kaybolur.
                logger.exception("%s kaydedilemedi", _Q_PATH.name)

    def apply_earth_feedback(self, suggested_threshold: float) -> None:
        if suggested_threshold >= 60:
            self._epsilon = min(0.35, self._epsilon + 0.02)
        else:
            self._epsilon = max(0.05, self._epsilon - 0.01)

    def get_rl_stats(self) -> Dict[str, Any]:
        return {
            "epsilon": round(self._epsilon, 4),
            "total_reward": round(self._total_reward, 2),
            "steps": self._steps,
            "q_table_size": len(self._q),
        }
