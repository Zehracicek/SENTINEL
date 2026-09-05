import { formatNumber, formatTimestamp, statusBadge, sensorLabel } from "../utils/formatters";

const CONNECTION_LABEL = {
  connected: "AKTİF",
  connecting: "BAĞLANIYOR",
  disconnected: "KESİNTİ",
};

export default function LiveStreamTable({ readings, wsStatus = "disconnected" }) {
  if (!readings || readings.length === 0) {
    const connected = wsStatus === "connected";
    return (
      <div className="n-hud p-6">
        <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: "#607080" }}>HAM_VERİ_AKIŞI</p>
        <div className="text-sm py-6 space-y-2" style={{ color: "#607080" }}>
          <p>[--:--:--] SENSÖR_VERİSİ_BEKLENİYOR...</p>
          <p>
            [--:--:--] BAĞLANTI_DURUMU:{" "}
            <span style={{ color: connected ? "#00FF88" : "#FF3366" }}>
              {CONNECTION_LABEL[wsStatus] ?? "KESİNTİ"}
            </span>
          </p>
          {connected && (
            <p style={{ color: "#506070" }}>
              [--:--:--] AKIŞ_BAĞLI — ilk telemetri turu bekleniyor.
            </p>
          )}
          {!connected && (
            <p style={{ color: "#506070" }}>
              [--:--:--] Sunucuya ulaşılamıyor; /health uç noktasını kontrol edin.
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="n-hud p-6">
      <div className="flex items-center justify-between mb-5">
        <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>HAM_VERİ_AKIŞI</p>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: "#00F2FF", boxShadow: "0 0 8px #00F2FF80" }} />
          <span className="text-xs uppercase tracking-wide" style={{ color: "#708090" }}>SON {readings.length} KAYIT</span>
        </div>
      </div>

      <div className="overflow-x-auto" style={{ background: "#050810", border: "1px solid #0D1520" }}>
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: "1px solid #0F1923" }}>
              {["ZAMAN", "KANAL", "SENSÖR", "DEĞER", "BİRİM", "SKOR", "DURUM", "İLETİM"].map((h, i) => (
                <th key={h} className={`py-3 px-4 text-xs font-bold uppercase tracking-wider ${i === 3 || i === 5 ? "text-right" : i >= 6 ? "text-center" : "text-left"}`}
                  style={{ color: "#607080" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {readings.map((r, i) => {
              const badge = statusBadge(r.anomaly_score);
              return (
                <tr key={r.id || i} style={{ borderBottom: "1px solid #0A0F18", background: r.is_anomaly ? "#FF33660A" : "transparent" }}>
                  <td className="py-3 px-4 text-sm" style={{ color: "#708090" }}>{formatTimestamp(r.created_at)}</td>
                  <td className="py-3 px-4 text-xs font-mono" style={{ color: "#506070" }}>{r.channel_id || "—"}</td>
                  <td className="py-3 px-4">
                    <span className="text-sm font-semibold" style={{ color: "#00F2FF", textShadow: "0 0 6px #00F2FF25" }}>{r.sensor_type}</span>
                    <span className="text-xs ml-2" style={{ color: "#607080" }}>{sensorLabel(r.sensor_type)}</span>
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-medium" style={{ color: "#BCC8D4" }}>{formatNumber(r.raw_value)}</td>
                  <td className="py-3 px-4 text-sm" style={{ color: "#708090" }}>{r.unit}</td>
                  <td className="py-3 px-4 text-right text-sm font-bold" style={{
                    color: r.anomaly_score >= 60 ? "#FF3366" : r.anomaly_score >= 30 ? "#FFAA00" : "#00FF88",
                    textShadow: r.anomaly_score >= 60 ? "0 0 10px #FF336650" : "none",
                  }}>{formatNumber(r.anomaly_score)}</td>
                  <td className="py-3 px-4 text-center">
                    <span className="inline-block px-3 py-1 text-xs font-bold uppercase tracking-wide" style={{
                      background: badge.bg, color: badge.text, border: `1px solid ${badge.border}`, boxShadow: `0 0 8px ${badge.text}10`,
                    }}>{badge.label}</span>
                  </td>
                  <td className="py-3 px-4 text-center text-sm font-bold" style={{
                    color: r.is_transmitted ? "#00FF88" : "#2A3A4D",
                    textShadow: r.is_transmitted ? "0 0 8px #00FF8840" : "none",
                  }}>{r.is_transmitted ? "İLET" : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
