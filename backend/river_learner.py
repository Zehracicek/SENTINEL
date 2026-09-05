"""Online anomaly scoring with River HalfSpaceTrees (.h5 kullanılmaz)."""

from __future__ import annotations

import logging
import pickle
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from river import anomaly

from channel_features import channel_code

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent / "data"
_STATE_PATH = _DATA_DIR / "river_model_state.pkl"
_SAVE_EVERY = 500

# Öznitelik şeması değiştiğinde artırın. Eski durum dosyası farklı bir uzayda
# eğitildiği için yüklenmemeli; aksi halde model her okumayı anomali sanar.
# v2: kanal özniteliği hash(channel_id) yerine kararlı channel_code() kullanır.
# v3: HalfSpaceTrees'e açık öznitelik sınırları verildi (aşağıya bakın).
_FEATURE_VERSION = 3

# HalfSpaceTrees sınır verilmediğinde HER özniteliği [0, 1] kabul eder. NASA
# telemetrisi ise test setinin min/max değerine göre [-1, 1] aralığına
# normalize edilmiştir; sınır belirtilmezse tüm negatif değerler "aralık dışı"
# sayılıp yüksek skor alır ve model sabit bir seriyi bile anomali sanar.
# Aralık dışına taşan gerçek uç değerler (ör. M-6'da 258) yine yüksek skor
# alır — istenen davranış budur.
_FEATURE_LIMITS = {"v": (-1.0, 1.0), "c": (0.0, 1.0)}

# HalfSpaceTrees'in ham skoru olasılık değildir; durağan normal veride bile
# 0.70–0.97 arasında oturur. Ham değeri doğrudan 100 ile çarpmak, nihai skora
# ~%60 ağırlıkla giren yaklaşık 45 puanlık sabit bir taban ekliyor ve eşiğin
# sürekli aşılmasına yol açıyordu. Bunun yerine ham skor, son
# _CALIBRATION_WINDOW örneğe göre yüzdelik sırasına çevrilir: 100, "son
# pencerede görülenlerin tamamından daha aykırı" anlamına gelir.
_CALIBRATION_WINDOW = 2000
_CALIBRATION_MIN_SAMPLES = 200


def _build_model() -> anomaly.HalfSpaceTrees:
    return anomaly.HalfSpaceTrees(
        n_trees=25,
        height=6,
        window_size=500,
        limits=_FEATURE_LIMITS,
        seed=42,
    )


class RiverLearner:
    def __init__(self) -> None:
        self._model: anomaly.HalfSpaceTrees = _build_model()
        self._n_samples_seen = 0
        self._model_version = 1
        self._last_saved: datetime | None = None
        # Kalibrasyon için son ham HST skorları (bkz. score_and_learn)
        self._recent_raw: deque[float] = deque(maxlen=_CALIBRATION_WINDOW)
        self._load_if_exists()

    def _feat(self, channel_id: str, raw_value: float) -> Dict[str, float]:
        return {"v": float(raw_value), "c": channel_code(channel_id)}

    def _load_if_exists(self) -> None:
        if not _STATE_PATH.is_file():
            return
        try:
            with open(_STATE_PATH, "rb") as f:
                data = pickle.load(f)
        except Exception:
            logger.warning(
                "%s okunamadı; model sıfırdan başlatılıyor.", _STATE_PATH.name
            )
            return

        if not isinstance(data, dict):
            return

        saved_version = int(data.get("feature_version", 1))
        if saved_version != _FEATURE_VERSION:
            logger.warning(
                "%s öznitelik sürümü %d, beklenen %d — eski durum yok sayılıyor "
                "ve model sıfırdan öğrenmeye başlıyor.",
                _STATE_PATH.name,
                saved_version,
                _FEATURE_VERSION,
            )
            return

        self._model = data.get("model", self._model)
        self._n_samples_seen = int(data.get("n_samples_seen", 0))
        self._model_version = int(data.get("model_version", 1))
        ts = data.get("last_saved")
        if ts:
            self._last_saved = datetime.fromisoformat(ts)

    def _save(self) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._model_version += 1
        self._last_saved = datetime.now(timezone.utc)
        payload = {
            "feature_version": _FEATURE_VERSION,
            "model": self._model,
            "n_samples_seen": self._n_samples_seen,
            "model_version": self._model_version,
            "last_saved": self._last_saved.isoformat(),
        }
        with open(_STATE_PATH, "wb") as f:
            pickle.dump(payload, f)

    def score_and_learn(self, channel_id: str, raw_value: float) -> float:
        """Ham HST skorunu son pencereye göre yüzdelik sıraya çevirip döndürür.

        Isınma sırasında (ilk _CALIBRATION_MIN_SAMPLES örnek) 0 döner; bu
        aşamada nihai skoru z-score / LSTM tabanı belirler.
        """
        x = self._feat(channel_id, raw_value)
        raw = float(self._model.score_one(x))
        self._model.learn_one(x)
        self._n_samples_seen += 1

        window = self._recent_raw
        if len(window) < _CALIBRATION_MIN_SAMPLES:
            calibrated = 0.0
        else:
            below = sum(1 for s in window if s < raw)
            calibrated = 100.0 * below / len(window)
        window.append(raw)

        if self._n_samples_seen % _SAVE_EVERY == 0:
            try:
                self._save()
            except Exception:
                # Sessiz kalırsa disk/izin sorunu yüzünden öğrenilen model
                # fark edilmeden kaybolur.
                logger.exception("%s kaydedilemedi", _STATE_PATH.name)
        return min(100.0, max(0.0, calibrated))

    def get_model_stats(self) -> Dict[str, Any]:
        return {
            "n_samples_seen": self._n_samples_seen,
            "model_version": self._model_version,
            "last_saved": self._last_saved.isoformat() if self._last_saved else None,
        }

    def reset_model(self) -> None:
        self._model = _build_model()
        self._n_samples_seen = 0
        self._model_version = 1
        self._last_saved = None
        self._recent_raw.clear()
        if _STATE_PATH.is_file():
            try:
                _STATE_PATH.unlink()
            except OSError:
                # Dosya silinemezse bir sonraki başlatmada eski durum geri
                # yüklenir; sıfırlama sessizce etkisiz kalmasın.
                logger.warning(
                    "%s silinemedi; yeniden başlatmada eski durum yüklenebilir.",
                    _STATE_PATH.name,
                )
