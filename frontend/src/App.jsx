import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import useWebSocket from "./hooks/useWebSocket";
import useAnomalyData from "./hooks/useAnomalyData";
import Dashboard from "./components/Dashboard";
import LandingPage from "./components/LandingPage";

const WS_PROTOCOL = window.location.protocol === "https:" ? "wss:" : "ws:";
const WS_URL = `${WS_PROTOCOL}//${window.location.host}/ws/live-feed`;

function SentinelShell() {
  const { status, messageBatch } = useWebSocket(WS_URL);
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
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/:sayfa" element={<SentinelShell />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
