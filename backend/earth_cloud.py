"""Simüle Earth/Cloud: model_updates üretir, RL epsilon besler.

Eşik önerisi rastgele jitter veya ham anomali oranından değil; mümkünse
Hundman dizi precision/recall (yoksa nokta metrikleri) üzerinden üretilir.
Düşük precision eşiği yükseltir, düşük recall düşürür.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from rl_agent import RLAgent


class EarthCloudSimulator:
    def __init__(self) -> None:
        self._model_version_counter = 0
        self._federated_round = 0
        self._orbiter_batches_since_cloud = 0
        self._last_feedback_basis = "idle"

    def on_orbiter_batch(self) -> None:
        self._orbiter_batches_since_cloud += 1

    def consume_if_ready(self, every_n: int = 20) -> bool:
        if self._orbiter_batches_since_cloud >= every_n:
            self._orbiter_batches_since_cloud = 0
            return True
        return False

    @staticmethod
    def suggest_threshold(metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """40–70 bandında eşik; formül: 55 + 18 × (recall − precision)."""
        low, high, mid = 40.0, 70.0, 55.0
        metrics = metrics or {}
        use_seq = bool(metrics.get("sequence_evaluated")) and int(
            metrics.get("sequence_indexed_readings") or 0
        ) >= 40
        if use_seq:
            precision = float(metrics.get("sequence_precision") or 0.0)
            recall = float(metrics.get("sequence_recall") or 0.0)
            basis = "sequence"
        elif int(metrics.get("evaluated_readings") or 0) >= 40:
            precision = float(metrics.get("precision") or 0.0)
            recall = float(metrics.get("recall") or 0.0)
            basis = "point"
        else:
            rate = float(metrics.get("recent_anomaly_rate") or 0.0)
            suggestion = mid + (high - mid) * (0.15 - min(1.0, rate)) * 4.0
            suggestion = round(max(low, min(high, suggestion)), 2)
            return {
                "threshold_suggestion": suggestion,
                "feedback_basis": "anomaly_rate",
                "precision": None,
                "recall": None,
            }

        suggestion = mid + 18.0 * (recall - precision)
        suggestion = round(max(low, min(high, suggestion)), 2)
        return {
            "threshold_suggestion": suggestion,
            "feedback_basis": basis,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
        }

    def build_update_payload(
        self,
        metrics: Optional[Dict[str, Any]] = None,
        recent_anomaly_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._model_version_counter += 1
        self._federated_round += 1
        payload_metrics = dict(metrics or {})
        if recent_anomaly_rate is not None and "recent_anomaly_rate" not in payload_metrics:
            payload_metrics["recent_anomaly_rate"] = recent_anomaly_rate
        derived = self.suggest_threshold(payload_metrics)
        self._last_feedback_basis = derived["feedback_basis"]
        return {
            "model_version": self._model_version_counter,
            "threshold_suggestion": derived["threshold_suggestion"],
            "federated_round": self._federated_round,
            "source": "earth_cloud",
            "feedback_basis": derived["feedback_basis"],
            "precision": derived["precision"],
            "recall": derived["recall"],
        }

    def apply_to_rl(self, rl: "RLAgent", threshold_suggestion: float) -> None:
        rl.apply_earth_feedback(threshold_suggestion)

    def get_dashboard_state(self, every_n: int = 20) -> Dict[str, Any]:
        pending = self._orbiter_batches_since_cloud
        return {
            "model_version": self._model_version_counter,
            "federated_round": self._federated_round,
            "orbiter_batches_since_cloud": pending,
            "batches_until_cloud_sync": max(0, every_n - pending),
            "cloud_sync_every_n_batches": every_n,
            "feedback_basis": self._last_feedback_basis,
        }
