import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ConnectionStatus from "./ConnectionStatus";
import MetricCards from "./MetricCards";
import AnomalyChart from "./AnomalyChart";
import LiveStreamTable from "./LiveStreamTable";
import BandwidthGauge from "./BandwidthGauge";
import AlertCenter from "./AlertCenter";
import PipelineAnimation from "./PipelineAnimation";
import SensorDetail from "./SensorDetail";
import DatasetInfo from "./DatasetInfo";
import RoverMap from "./RoverMap";
import Telemetry from "./Telemetry";
import TransmissionLog from "./TransmissionLog";
import UplinkQueue from "./UplinkQueue";
import OrbiterRelay from "./OrbiterRelay";
import EarthCloud from "./EarthCloud";
import RoverThinking from "./RoverThinking";
import EvaluationMetrics from "./EvaluationMetrics";
import NasaArchive from "./NasaArchive";
import { apiUrl } from "../utils/api";

/** URL: /{path} — alt çizgili sayfa adları */
export const NAV = [
  { id: "dashboard", path: "gosterge_paneli", label: "GÖSTERGE_PANELİ" },
  { id: "pipeline", path: "veri_akisi", label: "VERİ_AKIŞI" },
  { id: "anomalies", path: "anomali_tespit", label: "ANOMALİ_TESPİT" },
  { id: "sensor-detail", path: "sensor_detay", label: "SENSÖR_DETAY" },
  { id: "sensors", path: "telemetri", label: "TELEMETRİ" },
  { id: "rover-map", path: "rover_harita", label: "ROVER_HARİTA" },
  { id: "transmission", path: "iletim_analizi", label: "İLETİM_ANALİZİ" },
  { id: "uplink-queue", path: "uplink_kuyrugu", label: "UPLINK_KUYRUĞU" },
  { id: "dataset", path: "veri_seti", label: "VERİ_SETİ" },
  { id: "nasa", path: "nasa_arsiv", label: "NASA_ARŞİV" },
  { id: "orbiter", path: "orbiter_role", label: "ORBITER_RÖLE" },
  { id: "earth-cloud", path: "yer_istasyonu_bulut", label: "YER_İSTASYONU_BULUT" },
  { id: "rover-ai", path: "rover_zekasi", label: "ROVER_ZEKASİ" },
];

export default function Dashboard({
  wsStatus,
  readings,
  readingsByType,
  anomalies,
  chartData,
  stats,
  onAcknowledge,
  appendAnomaliesFromApi,
  orbiterStats,
  modelUpdates,
  rlRewardSeries,
  roverThinking,
}) {
  const { sayfa } = useParams();
  const navigate = useNavigate();
  const active =
    NAV.find((n) => n.path === sayfa)?.id ?? "dashboard";

  const [health, setHealth] = useState(null);

  useEffect(() => {
    if (!sayfa || !NAV.some((n) => n.path === sayfa)) {
      navigate("/gosterge_paneli", { replace: true });
    }
  }, [sayfa, navigate]);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      fetch(apiUrl("/health"))
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
        .then((j) => {
          if (!cancelled) setHealth(j);
        })
        .catch(() => {
          if (!cancelled) setHealth({ status: "unreachable" });
        });
    };
    load();
    const id = setInterval(load, 20000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const datasetMissing = health?.status === "degraded" || health?.dataset?.ready === false;
  const lstmMissing = health?.dataset?.ready && !health?.dataset?.has_smoothed_errors;

  const sol = stats?.rover?.sol ?? "—";
  const lat = stats?.rover?.lat ?? "—";
  const lon = stats?.rover?.lon ?? "—";
  const totalAnomaly = stats?.total_anomalies ?? 0;
  const bwSaved = stats?.bandwidth_saved_percent ?? 0;
  const totalPkt = stats?.total_packets ?? stats?.total_readings ?? 0;
  const timeStr = new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const lightOne = stats?.rover?.light_delay_min_one_way;
  const lightRt = stats?.rover?.light_delay_min_round_trip;
  const delayLabel =
    lightOne != null && lightRt != null
      ? `MARS→DÜNYA IŞIK GECİKMESİ: ${Number(lightOne).toFixed(1)} dk (tek yön) · ${Number(lightRt).toFixed(1)} dk (gidiş-dönüş) — veriler anlık değildir`
      : "MARS→DÜNYA IŞIK GECİKMESİ: ~3–22 dk (konuma bağlı) — veriler anlık değildir";

  const dataFlowLabel =
    wsStatus === "connected" ? "AKTİF" : wsStatus === "connecting" ? "BAĞLANIYOR" : "KESİNTİ";
  const signalLabel = wsStatus === "connected" ? "BAĞLI" : "DEĞİL";
  const signalColor = wsStatus === "connected" ? "#00FF88" : "#FF3366";

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: "#04060A" }}>

      {/* ÜST ÇUBUK */}
      <header className="h-11 shrink-0 flex items-center justify-between px-5" style={{ background: "#060910", borderBottom: "1px solid #0D1520" }}>
        <div className="flex items-center gap-5">
          <Link to="/" className="flex items-center gap-2 transition-opacity hover:opacity-90" title="Ana sayfa">
            <div className="w-1.5 h-4" style={{ background: "#00F2FF", boxShadow: "0 0 8px #00F2FF60" }} />
            <span className="text-base font-extrabold tracking-wider text-glow-cyan" style={{ color: "#00F2FF" }}>SENTİNEL_OS</span>
          </Link>
          <span className="text-xs" style={{ color: "#506070" }}>v1.0.4</span>
        </div>
        <div className="flex items-center gap-5">
          <ConnectionStatus status={wsStatus} />
          <span className="text-xs font-mono" style={{ color: "#607080" }}>{timeStr}</span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">

        {/* YAN PANEL */}
        <aside className="w-56 shrink-0 flex flex-col" style={{ background: "#060910", borderRight: "1px solid #0D1520" }}>
          <div className="px-5 pt-5 pb-3">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full" style={{ background: "#00F2FF", boxShadow: "0 0 6px #00F2FF80" }} />
              <span className="text-xs font-bold uppercase tracking-wider" style={{ color: "#8899AA" }}>ASTROBİYOLOJİ_BİRİMİ</span>
            </div>
            <p className="text-xs ml-4 uppercase tracking-widest" style={{ color: "#506070" }}>SEKTÖR: GALE KRATERİ (MSL)</p>
          </div>

          <div className="n-divider" />

          <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
            {NAV.map(item => {
              const on = active === item.id;
              return (
                <button key={item.id} type="button" onClick={() => navigate(`/${item.path}`)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-[13px] font-medium tracking-wide transition-all duration-200"
                  style={{
                    background: on ? "linear-gradient(90deg, #00F2FF10, transparent)" : "transparent",
                    color: on ? "#00F2FF" : "#708090",
                    borderLeft: on ? "2px solid #00F2FF" : "2px solid transparent",
                    textShadow: on ? "0 0 10px #00F2FF30" : "none",
                  }}>
                  {item.icon ? <span className="text-base shrink-0" aria-hidden>{item.icon}</span> : null}
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          <div className="n-divider" />
          <div className="px-5 py-4 space-y-1.5">
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>ROVER_KONUM</p>
            <p className="text-xs" style={{ color: "#607080" }}>ENL: <span style={{ color: "#99AAB8" }} className="font-semibold">{lat}</span></p>
            <p className="text-xs" style={{ color: "#607080" }}>BOY: <span style={{ color: "#99AAB8" }} className="font-semibold">{lon}</span></p>
            <p className="text-xs" style={{ color: "#607080" }}>SOL: <span style={{ color: "#00F2FF" }} className="font-bold text-glow-cyan">{sol}</span></p>
          </div>
        </aside>

        {/* ANA İÇERİK */}
        <main className="flex-1 flex flex-col overflow-hidden" style={{ background: "#04060A" }}>
          <div className="min-h-11 shrink-0 flex items-center justify-between px-6 py-1.5 gap-4" style={{ background: "#050810", borderBottom: "1px solid #0D1520" }}>
            <div className="flex flex-col justify-center gap-0.5 min-w-0">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-sm font-bold uppercase tracking-wide" style={{ color: "#99AAB8" }}>
                  {NAV.find(n => n.id === active)?.label}
                </span>
                <span className="text-xs" style={{ color: "#506070" }}>GERÇEK ZAMANLI ANALİZ | MARS-2026</span>
              </div>
              <p className="text-[10px] leading-snug uppercase tracking-wide" style={{ color: "#3A4A5C" }}>{delayLabel}</p>
            </div>
            <div className="flex items-center gap-2.5">
              {[
                { label: "ANOMALİ", value: totalAnomaly, color: "#FF3366", glow: "text-glow-red" },
                { label: "TASARRUF", value: `%${bwSaved.toFixed(1)}`, color: "#00FF88", glow: "text-glow-green" },
                { label: "PAKET", value: totalPkt, color: "#00F2FF", glow: "text-glow-cyan" },
              ].map(m => (
                <div key={m.label} className="flex items-center gap-2 px-3 py-1" style={{ background: "#080C14", border: "1px solid #0D1520" }}>
                  <span className="text-xs font-bold uppercase tracking-wider" style={{ color: "#607080" }}>{m.label}</span>
                  <span className={`text-sm font-extrabold ${m.glow}`} style={{ color: m.color }}>{m.value}</span>
                </div>
              ))}
            </div>
          </div>

          {(datasetMissing || lstmMissing || health?.status === "unreachable") && (
            <div
              className="shrink-0 px-6 py-2 text-[11px] font-mono leading-snug border-b"
              style={{
                background: datasetMissing || health?.status === "unreachable" ? "#1A0A0C" : "#12100A",
                borderColor: datasetMissing || health?.status === "unreachable" ? "#FF336640" : "#FFAA0030",
                color: "#99AAB8",
              }}
              role="status"
            >
              {health?.status === "unreachable" && (
                <span>Backend `/health` yanıt vermiyor. uvicorn ayakta mı?</span>
              )}
              {datasetMissing && (
                <span>
                  MSL test dosyaları yok — panel boş kalır.{" "}
                  <span style={{ color: "#00F2FF" }}>python scripts/fetch_dataset.py</span>
                </span>
              )}
              {!datasetMissing && lstmMissing && (
                <span>
                  LSTM `smoothed_errors` yok; skor z-score + River. İsteğe bağlı:{" "}
                  <span style={{ color: "#00F2FF" }}>python scripts/fetch_dataset.py --lstm</span>
                </span>
              )}
            </div>
          )}

          {stats == null && (
            <div
              className="shrink-0 px-6 py-1.5 text-[11px] font-mono leading-snug border-b flex items-center gap-2"
              style={{
                background: "#060D14",
                borderColor: "#00F2FF28",
                color: "#708090",
              }}
              role="status"
              aria-live="polite"
            >
              <span
                className="inline-block w-1.5 h-1.5 rounded-full shrink-0 animate-pulse"
                style={{
                  background: wsStatus === "connected" ? "#00F2FF" : "#FFAA00",
                  boxShadow: wsStatus === "connected" ? "0 0 8px #00F2FF80" : "0 0 6px #FFAA0060",
                }}
                aria-hidden
              />
              {wsStatus === "connected" && (
                <span>
                  <span style={{ color: "#99AAB8" }}>Canlı veri özeti yükleniyor…</span>{" "}
                  <span style={{ color: "#506070" }}>
                    İlk özet birkaç saniye içinde gelir; yaklaşık 5 saniyede bir yenilenir. Üstteki sayaçlar ve kartlardaki bekleme animasyonu hata değildir.
                  </span>
                </span>
              )}
              {wsStatus === "connecting" && (
                <span style={{ color: "#99AAB8" }}>WebSocket bağlantısı kuruluyor… Canlı özet bağlantı sonrası yüklenecek.</span>
              )}
              {wsStatus === "disconnected" && (
                <span>
                  <span style={{ color: "#FFAA00" }}>Sunucuya bağlı değil.</span>{" "}
                  <span style={{ color: "#506070" }}>Canlı özet ve tam metrikler için bağlantı gerekir.</span>
                </span>
              )}
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            {active === "dashboard" && (
              <>
                <MetricCards stats={stats} />
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                  <AnomalyChart data={chartData} />
                  <BandwidthGauge stats={stats} />
                </div>
                <EvaluationMetrics compact />
                <LiveStreamTable readings={readings} wsStatus={wsStatus} />
              </>
            )}
            {active === "pipeline" && <PipelineAnimation stats={stats} />}
            {active === "anomalies" && (
              <AlertCenter
                anomalies={anomalies}
                onAcknowledge={onAcknowledge}
                appendAnomaliesFromApi={appendAnomaliesFromApi}
              />
            )}
            {active === "sensor-detail" && (
              <SensorDetail readings={readings} readingsByType={readingsByType} anomalies={anomalies} />
            )}
            {active === "rover-map" && <RoverMap stats={stats} />}
            {active === "dataset" && <DatasetInfo />}
            {active === "nasa" && <NasaArchive />}
            {active === "sensors" && <Telemetry readings={readings} />}
            {active === "transmission" && <TransmissionLog stats={stats} />}
            {active === "uplink-queue" && <UplinkQueue statsQueue={stats?.uplink_queue} />}
            {active === "orbiter" && (
              <OrbiterRelay orbiterStats={orbiterStats} stats={stats} />
            )}
            {active === "earth-cloud" && (
              <EarthCloud
                modelUpdates={modelUpdates}
                rlRewardSeries={rlRewardSeries}
                stats={stats}
              />
            )}
            {active === "rover-ai" && (
              <RoverThinking entries={roverThinking || []} stats={stats} />
            )}
          </div>

          <footer className="min-h-7 shrink-0 flex flex-wrap items-center px-5 gap-x-8 gap-y-1 py-1 text-xs font-mono" style={{ background: "#060910", borderTop: "1px solid #0D1520" }}>
            <span style={{ color: "#00F2FF" }}>VERİ_AKIŞI: <span style={{ color: "#708090" }}>{dataFlowLabel}</span></span>
            <span style={{ color: "#506070" }}>AZIMUT: <span style={{ color: "#506070" }}>—</span></span>
            <span style={{ color: "#FF00FF" }}>KRİTİK: <span style={{ color: "#708090" }}>{totalAnomaly > 0 ? "AKTİF" : "YOK"}</span></span>
            <span style={{ color: "#506070" }}>TAMPON: <span style={{ color: "#506070" }}>—</span></span>
            <span style={{ color: "#506070" }}>
              IŞIK_GECİKMESİ:{" "}
              <span style={{ color: "#8899AA" }}>
                {lightOne != null ? `${Number(lightOne).toFixed(1)} dk (1Y)` : "—"}
              </span>
            </span>
            <span className="ml-auto font-bold uppercase tracking-wider" style={{ color: signalColor }}>SİNYAL: {signalLabel}</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
