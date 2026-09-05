import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import useWebSocket from "./hooks/useWebSocket";
import useAnomalyData from "./hooks/useAnomalyData";
import Dashboard from "./components/Dashboard";
import LandingPage from "./components/LandingPage";

function routerBasename() {
  const raw = import.meta.env.BASE_URL || "/";
  if (raw === "/") return undefined;
  return raw.replace(/\/$/, "");
}

function liveFeedWsUrl() {
  const explicit = String(import.meta.env.VITE_WS_URL || "").trim();
  if (explicit) return explicit;
  const apiBase = String(import.meta.env.VITE_API_BASE || "").trim();
  if (apiBase) {
    try {
      const u = new URL(apiBase);
      const proto = u.protocol === "https:" ? "wss:" : "ws:";
      return `${proto}//${u.host}/ws/live-feed`;
    } catch {
      /* geçersiz VITE_API_BASE */
    }
  }
  if (/\.github\.io$/i.test(window.location.hostname)) return "";
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws/live-feed`;
}

function SentinelShell() {
  const { status, messageBatch } = useWebSocket(liveFeedWsUrl());
  const {
    readings,
    readingsByType,
    anomalies,
    chartData,
    stats,
    orbiterStats,
    modelUpdates,
    rlRewardSeries,
    roverThinking,
    acknowledgeAnomaly,
    appendAnomaliesFromApi,
  } = useAnomalyData(messageBatch);

  return (
    <Dashboard
      wsStatus={status}
      readings={readings}
      readingsByType={readingsByType}
      anomalies={anomalies}
      chartData={chartData}
      stats={stats}
      orbiterStats={orbiterStats}
      modelUpdates={modelUpdates}
      rlRewardSeries={rlRewardSeries}
      roverThinking={roverThinking}
      onAcknowledge={acknowledgeAnomaly}
      appendAnomaliesFromApi={appendAnomaliesFromApi}
    />
  );
}

export default function App() {
  return (
    <BrowserRouter basename={routerBasename()}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/:sayfa" element={<SentinelShell />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
