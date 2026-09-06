import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import async_session
from earth_cloud import EarthCloudSimulator
from edge_processor import EdgeProcessor
from energy_controller import EnergyController
from orbiter_processor import OrbiterProcessor
from river_learner import RiverLearner
from rl_agent import RLAgent
from routers import (
    anomalies,
    evaluation as evaluation_router,
    model_updates as model_updates_router,
    nasa,
    orbiter as orbiter_router,
    sensor_data,
    settings as settings_router,
    uplink_queue,
    websocket as ws_router,
)
from routers.websocket import broadcast
from simulator import generate_sensor_readings, get_dataset_status, get_rover_state
import crud
import rover_ai

logger = logging.getLogger(__name__)

# Varsayılan yalnızca yerel geliştirme; üretim origin'i CORS_ALLOW_ORIGINS ile verilir
_DEFAULT_CORS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:8000,http://127.0.0.1:8000"
)
_cors_env = os.getenv("CORS_ALLOW_ORIGINS", _DEFAULT_CORS)
CORS_ALLOW_ORIGINS = [x.strip() for x in _cors_env.split(",") if x.strip()]

_sim_env = os.getenv("SENTINEL_SIM_INTERVAL_SECONDS") or os.getenv(
    "NIRVANA_SIM_INTERVAL_SECONDS", "10"
)
SIMULATION_INTERVAL_SEC = max(1.0, min(120.0, float(_sim_env)))

# Simülasyon her turda 12 kanal üretiyor. Drain hızı üretim hızının altında
# kalırsa uplink_queue sınırsız büyür, is_transmitted hiç true olmaz ve
# "bant tasarrufu" metriği yapay olarak şişer. Varsayılan kanal sayısına eşit.
UPLINK_DRAIN_BATCH = max(
    1, min(200, int(os.getenv("SENTINEL_UPLINK_DRAIN_BATCH", "12")))
)

river = RiverLearner()
energy = EnergyController()
rl = RLAgent()
orb = OrbiterProcessor()
earth = EarthCloudSimulator()
processor = EdgeProcessor(
    river_learner=river,
    energy_controller=energy,
    rl_agent=rl,
)


async def simulation_loop() -> None:
    while True:
        try:
            raw_readings = generate_sensor_readings()
            energy.record_processing_load(len(raw_readings))
            processed, anomaly_events, transmission_log = await processor.process_batch(raw_readings)

            async with async_session() as db:
                await crud.bulk_create_readings(db, processed, anomaly_events, transmission_log)
                await db.commit()

            for reading in processed:
                pub = {k: v for k, v in reading.items() if k != "_uplink_eligible"}
                await broadcast({"type": "sensor_reading", "data": pub})

            for event in anomaly_events:
                pub = {k: v for k, v in event.items() if not k.startswith("_")}
                pub["sensor_type"] = event.get("_sensor_type")
                pub["channel_id"] = event.get("_channel_id")
                await broadcast({"type": "anomaly_alert", "data": pub})

            await asyncio.sleep(SIMULATION_INTERVAL_SEC)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("simulation_loop failed; retrying after backoff")
            await asyncio.sleep(5)


async def stats_broadcast_loop() -> None:
    while True:
        try:
            async with async_session() as db:
                overview = await crud.get_overview_stats(db)
                qsnap = await crud.get_uplink_queue_snapshot(db)

            edge_stats = processor.get_stats()
            rover = get_rover_state()
            tr = overview["total_readings"]
            tx = overview.get("transmitted_readings", 0)
            await broadcast(
                {
                    "type": "stats_update",
                    "data": {
                        **overview,
                        **edge_stats,
                        "total_packets": tr,
                        "transmitted_packets": tx,
                        # Bant genişliği alanları veritabanındaki ölçülen
                        # byte toplamlarından gelir (edge_stats yalnızca süreç
                        # başlangıcından beri biriken değerleri tutar).
                        "compression_ratio": (
                            round(
                                overview["uplink_bytes"] / overview["baseline_bytes"], 6
                            )
                            if overview["baseline_bytes"] > 0
                            else 0.0
                        ),
                        "bandwidth_saved_percent": overview["bandwidth_saved_percent"],
                        "total_bytes_saved": overview["total_bytes_saved"],
                        "packet_ratio": overview["packet_ratio"],
                        "rover": rover,
                        "uplink_queue": qsnap,
                        "river_stats": river.get_model_stats(),
                        "energy_stats": energy.get_energy_stats(),
                        "rl_stats": rl.get_rl_stats(),
                        "rover_thinking_enabled": processor.rover_thinking_enabled,
                        "groq_configured": rover_ai.get_usage_stats().get("enabled", False),
                        "simulation_interval_seconds": SIMULATION_INTERVAL_SEC,
                        "earth_cloud_state": earth.get_dashboard_state(),
                        "orbiter_stats": orb.get_ws_stats(),
                    },
                }
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("stats_broadcast_loop failed")
        await asyncio.sleep(5)


async def uplink_drain_loop() -> None:
    while True:
        try:
            await asyncio.sleep(10)
            async with async_session() as db:
                sent_payloads = await crud.drain_uplink_queue(
                    db, processor, max_items=UPLINK_DRAIN_BATCH
                )
                await db.commit()
            for row in sent_payloads:
                await broadcast({"type": "sensor_reading", "data": row})
            if sent_payloads:
                async with async_session() as db:
                    snap = await crud.get_uplink_queue_snapshot(db)
                await broadcast({"type": "uplink_queue_update", "data": snap})
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("uplink_drain_loop failed")


async def energy_update_loop() -> None:
    while True:
        try:
            await asyncio.sleep(10)
            energy.tick_battery()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("energy_update_loop failed")


async def orbiter_drain_loop() -> None:
    while True:
        try:
            await asyncio.sleep(15)
            async with async_session() as db:
                await crud.process_orbiter_drain(db, orb, max_items=24)
                await db.commit()
            meta = orb.tick_flush_if_due()
            if meta:
                async with async_session() as db:
                    await crud.insert_orbiter_relay_log(db, meta)
                    await db.commit()
                await broadcast({"type": "orbiter_stats", "data": orb.get_ws_stats()})
                earth.on_orbiter_batch()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("orbiter_drain_loop failed")


async def earth_sync_loop() -> None:
    while True:
        try:
            await asyncio.sleep(8)
            if not earth.consume_if_ready(20):
                continue
            async with async_session() as db:
                metrics = await crud.get_detection_metrics(db)
                rate = await crud.get_recent_anomaly_rate(db)
                metrics["recent_anomaly_rate"] = rate
                payload = earth.build_update_payload(metrics)
                await crud.create_model_update(db, payload)
                await db.commit()
            earth.apply_to_rl(rl, payload["threshold_suggestion"])
            await broadcast(
                {
                    "type": "model_update",
                    "data": {
                        "model_version": payload["model_version"],
                        "threshold_suggestion": payload["threshold_suggestion"],
                        "federated_round": payload["federated_round"],
                        "feedback_basis": payload.get("feedback_basis"),
                        "precision": payload.get("precision"),
                        "recall": payload.get("recall"),
                    },
                }
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("earth_sync_loop failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    sim_task = asyncio.create_task(simulation_loop())
    stats_task = asyncio.create_task(stats_broadcast_loop())
    uplink_task = asyncio.create_task(uplink_drain_loop())
    energy_task = asyncio.create_task(energy_update_loop())
    orbiter_task = asyncio.create_task(orbiter_drain_loop())
    earth_task = asyncio.create_task(earth_sync_loop())
    yield
    bg_tasks = (
        sim_task,
        stats_task,
        uplink_task,
        energy_task,
        orbiter_task,
        earth_task,
    )
    for t in bg_tasks:
        t.cancel()
    await asyncio.gather(*bg_tasks, return_exceptions=True)
    await rover_ai.aclose()


app = FastAPI(
    title="Sentinel — Astrobiyolojik Sensör Yükü Veri Mimarisi API",
    description=(
        "Mars rover simülasyonundan gelen uçta işlenmiş sensör verisi; "
        "WebSocket canlı akış, uplink kuyruğu, orbiter rölesi ve yer istasyonu eşik geri bildirimi."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings_router.router)
app.include_router(sensor_data.router)
app.include_router(anomalies.router)
app.include_router(uplink_queue.router)
app.include_router(nasa.router)
app.include_router(orbiter_router.router)
app.include_router(model_updates_router.router)
app.include_router(evaluation_router.router)
app.include_router(ws_router.router)


@app.get("/health")
async def health():
    dataset = get_dataset_status()
    return {
        "status": "ok" if dataset["ready"] else "degraded",
        "service": "sentinel-api",
        "dataset": dataset,
        # Groq harcaması burada izlenir: kota, başarısız çağrı ve atlama sayıları
        "rover_ai": rover_ai.get_usage_stats(),
        "energy": energy.get_energy_stats(),
        "detail": (
            None
            if dataset["ready"]
            else (
                "NASA MSL veri seti yüklenemedi; simülasyon okuma üretmiyor. "
                "python scripts/fetch_dataset.py ile indirin."
            )
        ),
    }
