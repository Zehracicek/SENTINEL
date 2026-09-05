import asyncio
import logging
import os
import uuid
import random
from collections import OrderedDict, defaultdict, deque
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np

import rover_ai
from compressor import compress_readings_delta_deflate, readings_to_f64_payload
from routers.websocket import broadcast

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from energy_controller import EnergyController
    from river_learner import RiverLearner
    from rl_agent import RLAgent

ANOMALY_TYPE_MAP: Dict[str, str] = {
    "CH4": "methane_spike",
    "MOIST": "moisture_anomaly",
    "SPEC": "spectral_deviation",
    "TEMP": "temperature_extreme",
    "UV": "radiation_anomaly",
    "O2": "atmospheric_anomaly",
    "CO2": "atmospheric_anomaly",
    "PRESS": "pressure_anomaly",
}

PRIORITY_MAP: Dict[str, int] = {
    "organic_molecule": 10,
    "methane_spike": 8,
    "spectral_deviation": 7,
    "moisture_anomaly": 6,
    "radiation_anomaly": 5,
    "atmospheric_anomaly": 5,
    "pressure_anomaly": 4,
    "temperature_extreme": 4,
}

DSN_WINDOWS = ["Goldstone-DSS14", "Canberra-DSS43", "Madrid-DSS63"]

# Kanal başına saklanan geçmiş örnek sayısı ve novelty mesafe ölçeği.
# Telemetri [-1, 1] aralığında normalize; 0.25 ölçeğinde ~0.30 birimlik bir
# sapma benzerliği 0.3'ün altına düşürür ve okuma "yeni imza" sayılır.
_NOVELTY_PER_CHANNEL = 500
_NOVELTY_DISTANCE_SCALE = 0.25
_NOVELTY_SIMILARITY_THRESHOLD = 0.3

# Ödül eşleştirmesi için saklanan azami karar sayısı (kuyruk derinliğinden büyük).
_RL_DECISION_MEMORY = 5000


class EdgeProcessor:
    def __init__(
        self,
        river_learner: Optional["RiverLearner"] = None,
        energy_controller: Optional["EnergyController"] = None,
        rl_agent: Optional["RLAgent"] = None,
    ) -> None:
        self._river = river_learner
        self._energy = energy_controller
        self._rl = rl_agent
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._max_history = 500
        self._total_packets = 0
        self._transmitted_packets = 0
        self._payload_serialized_total = 0
        self._payload_compressed_total = 0
        self._last_payload_serialized = 0
        self._last_payload_compressed = 0
        self._zlib_level = 6
        # Filtresiz/sıkıştırmasız referans hacim (bkz. get_stats)
        self._baseline_bytes_total = 0
        self._novelty_hist: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=_NOVELTY_PER_CHANNEL)
        )
        self._last_rl_state: Optional[Tuple[float, float, bool]] = None
        self._last_rl_action_idx: int = 1
        # reading_id -> (mean_score, batarya, novelty, action_idx)
        # Uplink drain'i batch'lerce sonra geldiği için ödül, paketi doğuran
        # kararın durumuna yazılmalı; en son batch'in durumuna değil.
        self._rl_decisions: "OrderedDict[str, Tuple[float, float, bool, int]]" = (
            OrderedDict()
        )
        self._rover_think_sem = asyncio.Semaphore(2)
        self.rover_thinking_enabled: bool = False

    def _schedule_rover_think(
        self,
        reading: dict,
        processed: List[dict],
        adj: int,
        action_idx: int,
        energy_level: float,
    ) -> None:
        if not self.rover_thinking_enabled:
            return
        task = asyncio.create_task(
            self._rover_think_background(reading, processed, adj, action_idx, energy_level)
        )

        def _log_fail(t: asyncio.Task) -> None:
            try:
                t.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("rover_think_background failed")

        task.add_done_callback(_log_fail)

    async def _rover_think_background(
        self,
        reading: dict,
        processed: List[dict],
        adj: int,
        action_idx: int,
        energy_level: float,
    ) -> None:
        if not self.rover_thinking_enabled:
            return
        delay = max(0.0, min(120.0, float(os.getenv("ROVER_THINK_DELAY_SECONDS", "10"))))
        if delay > 0:
            await asyncio.sleep(delay)

        rl_labels = {0: "eşik Δ-5", 1: "eşik nötr", 2: "eşik Δ+5"}
        ch = str(reading.get("_chan_id") or reading.get("channel_id") or reading["sensor_type"])
        anomaly_type = self._detect_anomaly_type(reading, processed)
        pri = PRIORITY_MAP.get(anomaly_type, 4)
        if reading.get("is_novel"):
            pri = min(10, pri + 2)
        rl_suggestion = f"RL Δ={adj} — {rl_labels.get(action_idx, f'eylem_{action_idx}')}"
        ctx = {
            "channel_id": ch,
            "sensor_type": reading["sensor_type"],
            "raw_value": reading["raw_value"],
            "anomaly_score": reading["anomaly_score"],
            "river_score": reading.get("_river_score", 0),
            "lstm_score": reading.get("_lstm_score", 0),
            "is_novel": bool(reading.get("is_novel")),
            "novelty_similarity": float(reading.get("_novelty_similarity", 0)),
            "energy_level": energy_level,
            "rl_suggestion": rl_suggestion,
            "scientific_priority": int(pri),
            "anomaly_type": anomaly_type,
            "uplink_eligible": bool(reading.get("_uplink_eligible")),
        }
        async with self._rover_think_sem:
            try:
                out = await asyncio.wait_for(rover_ai.think(ctx), timeout=10.0)
            except asyncio.TimeoutError:
                out = {
                    "thinking": "AI thinking devre dışı",
                    "steps": [],
                    "decision": "TX" if reading.get("_uplink_eligible") else "DROP",
                    "duration_ms": 0,
                    "model": "fallback",
                }
        ts = datetime.now(timezone.utc).isoformat()
        uplink_ok = bool(reading.get("_uplink_eligible"))
        await broadcast(
            {
                "type": "rover_thinking",
                "data": {
                    "channel_id": ch,
                    "anomaly_score": float(reading["anomaly_score"]),
                    "thinking": out.get("thinking", ""),
                    "steps": out.get("steps") or [],
                    "decision": out.get("decision", "TX"),
                    "duration_ms": int(out.get("duration_ms", 0)),
                    "model": out.get("model", "fallback"),
                    "timestamp": ts,
                    "is_novel": bool(reading.get("is_novel")),
                    "novelty_similarity": float(reading.get("_novelty_similarity", 0)),
                    "energy_level": round(energy_level, 1),
                    "uplink_eligible": uplink_ok,
                },
            }
        )

    @staticmethod
    def _channel_key(reading: dict) -> str:
        return str(
            reading.get("_chan_id") or reading.get("channel_id") or reading["sensor_type"]
        )

    def _update_history(self, channel_key: str, value: float) -> None:
        self._history[channel_key].append(value)
        if len(self._history[channel_key]) > self._max_history:
            self._history[channel_key] = self._history[channel_key][-self._max_history :]

    def _compute_z_style_score(self, reading: dict) -> float:
        channel_key = self._channel_key(reading)
        value = reading["raw_value"]
        history = self._history[channel_key]

        if len(history) < 10:
            sensor_std = 0.3
            sensor_mean = 0.0
        else:
            sensor_mean = float(np.mean(history))
            sensor_std = float(np.std(history))

        if sensor_std < 1e-6:
            sensor_std = 0.01

        z_score = abs(value - sensor_mean) / sensor_std
        return round(min(100.0, z_score * 25.0), 2)

    def _compute_base_scores(self, reading: dict) -> Tuple[float, float]:
        smoothed_err = reading.get("_smoothed_error")
        if smoothed_err is not None:
            lstm_s = min(100.0, float(smoothed_err) * 300.0)
            return round(lstm_s, 2), lstm_s
        z_s = self._compute_z_style_score(reading)
        return z_s, z_s

    def _novelty_check(self, channel_id: str, raw_value: float) -> Tuple[bool, float]:
        """Aynı kanalda daha önce görülen en yakın değere olan uzaklık.

        Önceki sürüm iki boyutlu bir vektörün kosinüs benzerliğine bakıyordu;
        kosinüs ölçekten bağımsız olduğu için telemetri değerinin büyüklüğü
        tamamen göz ardı ediliyor, fiilen yalnızca işaret değişimi ölçülüyordu.
        Burada benzerlik, en yakın komşuya olan mutlak uzaklıktan türetilir:
        1.0 = birebir görülmüş, 0.0'a yaklaştıkça daha yeni bir imza.
        """
        hist = self._novelty_hist[channel_id]
        if not hist:
            hist.append(float(raw_value))
            return False, 1.0

        arr = np.fromiter(hist, dtype=np.float64, count=len(hist))
        distance = float(np.min(np.abs(arr - float(raw_value))))
        similarity = float(np.exp(-distance / _NOVELTY_DISTANCE_SCALE))
        hist.append(float(raw_value))
        return similarity < _NOVELTY_SIMILARITY_THRESHOLD, similarity

    def _determine_severity(self, score: float) -> str:
        if score >= 90:
            return "CRITICAL"
        if score >= 70:
            return "HIGH"
        if score >= 50:
            return "MEDIUM"
        return "LOW"

    def _detect_anomaly_type(self, reading: dict, all_readings: List[dict]) -> str:
        anomalous_sensors = {r["sensor_type"] for r in all_readings if r.get("_is_anomaly_final")}
        if len(anomalous_sensors) >= 3:
            return "organic_molecule"
        return ANOMALY_TYPE_MAP.get(reading["sensor_type"], "temperature_extreme")

    def _build_description(self, anomaly_type: str, reading: dict, score: float) -> str:
        chan_label = reading.get("_chan_label", reading["sensor_type"])
        chan_id = reading.get("_chan_id", "")
        value = reading["raw_value"]
        pred = reading.get("_prediction")

        pred_info = f" LSTM tahmini: {pred:.4f}," if pred is not None else ""

        descriptions = {
            "organic_molecule": f"Çoklu sensör anomalisi — olası organik molekül imzası. Kanal: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}.",
            "methane_spike": f"Metan konsantrasyonu sıçraması: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}. Olası yeraltı salınımı.",
            "moisture_anomaly": f"Beklenmeyen nem okuması: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}. Yeraltı buz etkileşimi olabilir.",
            "spectral_deviation": f"Spektral yoğunluk sapması: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}. Bilinmeyen mineral imzası.",
            "temperature_extreme": f"Sıcaklık ekstremi: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}. Nominal aralık dışında.",
            "radiation_anomaly": f"Radyasyon anomalisi: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}. UV/radyasyon seviyesi anormal.",
            "atmospheric_anomaly": f"Atmosferik anomali: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}. Gaz konsantrasyonu sapması.",
            "pressure_anomaly": f"Basınç anomalisi: {chan_label} ({chan_id}), değer: {value:.4f},{pred_info} skor: {score}. Atmosferik basınç sapması.",
        }
        return descriptions.get(anomaly_type, f"Anomali: {chan_label}, değer {value:.4f}, skor {score}.")

    async def process_batch(self, raw_readings: List[dict]) -> Tuple[List[dict], List[dict], Optional[dict]]:
        anomaly_events: List[dict] = []
        temps: List[dict] = []
        for reading in raw_readings:
            value = reading["raw_value"]
            cid = self._channel_key(reading)
            self._update_history(cid, value)

            base_for_hybrid, lstm_or_z_display = self._compute_base_scores(reading)
            smoothed_err = reading.get("_smoothed_error")
            if self._river is not None:
                river_s = self._river.score_and_learn(cid, value)
                if smoothed_err is not None:
                    score = round(base_for_hybrid * 0.5 + river_s * 0.5, 2)
                else:
                    score = round(base_for_hybrid * 0.4 + river_s * 0.6, 2)
            else:
                river_s = float(lstm_or_z_display)
                score = round(base_for_hybrid, 2)

            reading["_river_score"] = round(float(river_s), 2)
            reading["_lstm_score"] = round(float(lstm_or_z_display), 2)
            is_novel, nov_sim = self._novelty_check(cid, value)
            reading["_novelty_similarity"] = round(float(nov_sim), 4)

            reading["_pending_score"] = score
            reading["_is_novel"] = is_novel
            reading["_lstm_or_z"] = lstm_or_z_display
            temps.append(reading)

        scores = [float(r["_pending_score"]) for r in temps]
        mean_score = float(np.mean(scores)) if scores else 0.0
        novel_any = any(r.get("_is_novel") for r in temps)

        base_th, zlib_lvl = (50, 6)
        if self._energy is not None:
            base_th, zlib_lvl = self._energy.get_threshold_and_zlib()
        adj = 0
        action_idx = 1
        bat = self._energy.get_battery_level() if self._energy else 50.0
        if self._rl is not None and self._energy is not None:
            adj, action_idx = self._rl.get_threshold_adjustment(mean_score, bat, novel_any)
        threshold = int(max(40, min(85, base_th + adj)))
        self._zlib_level = zlib_lvl
        self._last_rl_state = (mean_score, bat, novel_any)
        self._last_rl_action_idx = action_idx

        processed = []
        for reading in temps:
            score = float(reading.pop("_pending_score"))
            is_novel = bool(reading.pop("_is_novel"))
            reading.pop("_lstm_or_z", None)

            is_score_anomaly = score >= threshold
            is_anomaly = is_score_anomaly
            reading["anomaly_score"] = score
            reading["is_anomaly"] = is_anomaly
            reading["is_transmitted"] = False
            reading["is_novel"] = is_novel
            reading["_is_anomaly_final"] = is_anomaly
            reading["_uplink_eligible"] = score >= threshold

            if reading["_uplink_eligible"]:
                self._remember_rl_decision(
                    str(reading["id"]), mean_score, bat, novel_any, action_idx
                )

            self._total_packets += 1

            internal_keys = [k for k in reading if k.startswith("_")]
            clean_reading = {k: v for k, v in reading.items() if not k.startswith("_")}
            processed.append({**clean_reading, **{k: reading[k] for k in internal_keys}})

        anomalous = [r for r in processed if r.get("_is_anomaly_final")]
        for reading in anomalous:
            anomaly_type = self._detect_anomaly_type(reading, processed)
            severity = self._determine_severity(reading["anomaly_score"])
            priority = PRIORITY_MAP.get(anomaly_type, 4)
            if reading.get("is_novel"):
                priority = min(10, priority + 2)

            anomaly_events.append(
                {
                    "id": uuid.uuid4(),
                    "reading_id": reading["id"],
                    "_sensor_type": reading["sensor_type"],
                    "_channel_id": str(reading.get("_chan_id") or ""),
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "description": self._build_description(
                        anomaly_type, reading, reading["anomaly_score"]
                    ),
                    "scientific_priority": priority,
                    "acknowledged": False,
                    "created_at": datetime.now(timezone.utc),
                }
            )

        energy_level = float(self._energy.get_battery_level()) if self._energy else 50.0
        for reading in processed:
            if float(reading.get("anomaly_score", 0)) < 50:
                continue
            self._schedule_rover_think(reading, processed, adj, action_idx, energy_level)

        self._last_payload_serialized = 0
        self._last_payload_compressed = 0

        transmission_log = None
        if self._total_packets > 0:
            total = len(raw_readings)
            eligible = [r for r in processed if r.get("_uplink_eligible")]
            transmitted = len(eligible)

            # Referans: hiç filtrelemeyen ve sıkıştırmayan bir sistemin bu batch
            # için göndereceği hacim. Gerçekten gönderilen ise yalnızca eşiği
            # geçen okumaların delta + DEFLATE çıktısı. İkisinin farkı mimarinin
            # sağladığı gerçek kazanç — daha önce burada uydurma bir
            # "256 byte/paket" sabiti kullanılıyordu ve tasarruf, verinin toplam
            # hacminden kat kat büyük çıkıyordu.
            baseline_bytes = len(readings_to_f64_payload(processed))
            uplink_bytes = compress_readings_delta_deflate(
                eligible, zlib_level=self._zlib_level
            ).compressed_bytes

            self._baseline_bytes_total += baseline_bytes

            transmission_log = {
                "id": uuid.uuid4(),
                "batch_id": uuid.uuid4(),
                "total_packets": total,
                "transmitted_packets": transmitted,
                "baseline_bytes": baseline_bytes,
                "uplink_bytes": uplink_bytes,
                "bytes_saved": max(0, baseline_bytes - uplink_bytes),
                "compression_ratio": (
                    round(uplink_bytes / baseline_bytes, 4) if baseline_bytes else 1.0
                ),
                "packet_ratio": round(transmitted / total, 4) if total else 1.0,
                "transmission_window": random.choice(DSN_WINDOWS),
                "created_at": datetime.now(timezone.utc),
            }

        db_readings = []
        for r in processed:
            row = {k: v for k, v in r.items() if not k.startswith("_")}
            row["channel_id"] = str(r.get("_chan_id") or "")
            row["ground_truth_anomaly"] = bool(r.get("_is_labeled_anomaly", False))
            row["is_novel"] = bool(r.get("is_novel", False))
            if r.get("_idx") is not None:
                row["replay_index"] = int(r["_idx"])
            if r.get("_uplink_eligible"):
                row["_uplink_eligible"] = True
            db_readings.append(row)

        return db_readings, anomaly_events, transmission_log

    def record_uplink_batch(self, sent_readings: List[dict]) -> None:
        if not sent_readings:
            return
        self._transmitted_packets += len(sent_readings)
        comp = compress_readings_delta_deflate(
            sent_readings, zlib_level=self._zlib_level
        )
        if comp.serialized_bytes > 0:
            self._payload_serialized_total += comp.serialized_bytes
            self._payload_compressed_total += comp.compressed_bytes
        self._last_payload_serialized = comp.serialized_bytes
        self._last_payload_compressed = comp.compressed_bytes

        # Enerji döngüsünü kapatır: iletim ve sıkıştırma bataryadan düşülür,
        # bu da bir sonraki turun eşiğini etkiler.
        if self._energy is not None:
            self._energy.record_uplink_energy(len(sent_readings), self._zlib_level)

    def _remember_rl_decision(
        self,
        reading_id: str,
        mean_score: float,
        battery: float,
        novelty: bool,
        action_idx: int,
    ) -> None:
        self._rl_decisions[reading_id] = (mean_score, battery, novelty, action_idx)
        while len(self._rl_decisions) > _RL_DECISION_MEMORY:
            self._rl_decisions.popitem(last=False)

    @staticmethod
    def _uplink_reward(reading: dict) -> float:
        score = float(reading.get("anomaly_score", 0))
        reward = 0.0
        if score >= 72 and reading.get("is_anomaly"):
            reward += 10.0
        if score < 58:
            reward -= 5.0
        if reading.get("is_novel"):
            reward += 5.0
        return reward

    def apply_rl_rewards_after_uplink(self, sent_readings: List[dict]) -> None:
        """Her paketin ödülünü, o paketi kuyruğa alan kararın durumuna yazar."""
        if not sent_readings or self._rl is None:
            return
        for reading in sent_readings:
            decision = self._rl_decisions.pop(str(reading.get("id")), None)
            if decision is None:
                # Sunucu yeniden başlamış olabilir; eşleşmeyen paket atlanır.
                continue
            mean_score, battery, novelty, action_idx = decision
            self._rl.update_from_action(
                mean_score, battery, novelty, action_idx, self._uplink_reward(reading)
            )

    def get_stats(self) -> dict:
        """Bant genişliği metrikleri — hepsi ölçülmüş byte değerlerine dayanır.

        `baseline` = üretilen tüm okumaların serialize edilmiş hacmi (filtresiz,
        sıkıştırmasız). `uplink` = gerçekten iletilen batch'lerin DEFLATE sonrası
        hacmi. Tasarruf bu ikisinin farkıdır; hem filtrelemenin hem sıkıştırmanın
        katkısını birlikte içerir.
        """
        baseline = self._baseline_bytes_total
        uplink = self._payload_compressed_total
        byte_ratio = round(uplink / baseline, 6) if baseline > 0 else 0.0

        ser = self._payload_serialized_total
        deflate_ratio = round(uplink / ser, 6) if ser > 0 else 0.0
        last_ser = self._last_payload_serialized
        last_z = self._last_payload_compressed
        last_deflate_ratio = round(last_z / last_ser, 6) if last_ser > 0 else 0.0

        return {
            "total_packets": self._total_packets,
            "transmitted_packets": self._transmitted_packets,
            # Byte tabanlı: gönderilen hacim / filtresiz referans hacim
            "compression_ratio": byte_ratio,
            "bandwidth_saved_percent": (
                round((1 - byte_ratio) * 100, 2) if baseline > 0 else 0.0
            ),
            "total_bytes_saved": max(0, baseline - uplink),
            "baseline_bytes": baseline,
            "uplink_bytes": uplink,
            # Paket sayısı tabanlı oran (eski "compression_ratio" anlamı)
            "packet_ratio": (
                round(self._transmitted_packets / self._total_packets, 4)
                if self._total_packets > 0
                else 0.0
            ),
            "packet_filter_saved_percent": (
                round(
                    (1 - self._transmitted_packets / self._total_packets) * 100,
                    2,
                )
                if self._total_packets > 0
                else 0.0
            ),
            # Yalnızca sıkıştırmanın katkısı (filtreleme hariç)
            "payload_serialized_bytes": ser,
            "payload_deflated_bytes": uplink,
            "payload_deflate_ratio": deflate_ratio,
            "payload_deflate_savings_percent": (
                round((1 - deflate_ratio) * 100, 2) if ser > 0 else 0.0
            ),
            "last_batch_payload_bytes": last_ser,
            "last_batch_deflated_bytes": last_z,
            "last_batch_deflate_ratio": last_deflate_ratio,
        }
