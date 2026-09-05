import { useState, useMemo } from "react";
import { formatNumber, formatTimestamp, sensorLabel } from "../utils/formatters";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";

const SENSOR_COLORS = {
  TEMP: "#00F2FF", CH4: "#FF00FF", O2: "#00FF88", CO2: "#FFAA00",
  MOIST: "#7000FF", SPEC: "#FF3366", UV: "#FF8800", PRESS: "#00F2FF",
};

export default function Telemetry({ readings }) {
  const [filter, setFilter] = useState("ALL");

  const types = useMemo(() => [...new Set(readings.map(r => r.sensor_type))].sort(), [readings]);
  const filtered = filter === "ALL" ? readings : readings.filter(r => r.sensor_type === filter);

  const sensorSummary = useMemo(() => {
    const map = {};
    readings.forEach(r => {
      if (!map[r.sensor_type]) map[r.sensor_type] = { count: 0, sum: 0, anomalies: 0, last: null };
      map[r.sensor_type].count++;
      map[r.sensor_type].sum += r.raw_value;
      if (r.is_anomaly) map[r.sensor_type].anomalies++;
      if (!map[r.sensor_type].last) map[r.sensor_type].last = r;
    });
    return Object.entries(map).map(([type, d]) => ({
      type, count: d.count, avg: d.sum / d.count, anomalies: d.anomalies, last: d.last,
    }));
  }, [readings]);

  const miniCharts = useMemo(() => {
    const map = {};
    readings.forEach(r => {
      if (!map[r.sensor_type]) map[r.sensor_type] = [];
      if (map[r.sensor_type].length < 20) {
        map[r.sensor_type].push({ t: formatTimestamp(r.created_at), v: r.raw_value });
      }
    });
    return map;
  }, [readings]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>TELEMETRİ_PANOSU</p>
          <p className="text-sm mt-1" style={{ color: "#708090" }}>Tüm sensörlerden gelen anlık telemetri verisi akışı</p>
        </div>
        <div className="flex gap-1">
          <button onClick={() => setFilter("ALL")} className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-all"
            style={{ background: filter === "ALL" ? "#00F2FF15" : "transparent", border: `1px solid ${filter === "ALL" ? "#00F2FF50" : "#0D1520"}`, color: filter === "ALL" ? "#00F2FF" : "#506070" }}>
            TÜMÜ
          </button>
          {types.map(t => (
            <button key={t} onClick={() => setFilter(t)} className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-all"
              style={{ background: filter === t ? `${SENSOR_COLORS[t]}15` : "transparent", border: `1px solid ${filter === t ? `${SENSOR_COLORS[t]}50` : "#0D1520"}`, color: filter === t ? SENSOR_COLORS[t] : "#506070" }}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Sensor summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {sensorSummary.map(s => {
          const color = SENSOR_COLORS[s.type] || "#607080";
          const data = (miniCharts[s.type] || []).slice().reverse();
          return (
            <div key={s.type} className="n-hud p-4 cursor-pointer transition-all" onClick={() => setFilter(s.type)}
              style={{ borderColor: filter === s.type ? `${color}40` : undefined }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold" style={{ color }}>{s.type}</span>
                <span className="text-xs" style={{ color: "#506070" }}>{sensorLabel(s.type)}</span>
              </div>
              {data.length > 2 && (
                <ResponsiveContainer width="100%" height={40}>
                  <AreaChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
                    <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`${color}15`} dot={false} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
              <div className="flex justify-between mt-2">
                <span className="text-xs" style={{ color: "#506070" }}>Son: <span style={{ color: "#8899AA" }}>{s.last ? formatNumber(s.last.raw_value, 3) : "—"}</span></span>
                <span className="text-xs" style={{ color: s.anomalies > 0 ? "#FF3366" : "#506070" }}>Anomali: {s.anomalies}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Data table */}
      <div className="n-hud p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>
            {filter === "ALL" ? "TÜM_SENSÖR_VERİSİ" : `${filter}_VERİSİ`}
          </p>
          <span className="text-xs" style={{ color: "#506070" }}>{filtered.length} kayıt</span>
        </div>
        <div className="overflow-x-auto" style={{ background: "#050810", border: "1px solid #0D1520" }}>
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: "1px solid #0F1923" }}>
                {["ZAMAN", "SENSÖR", "TİP", "DEĞER", "BİRİM", "SKOR", "DURUM"].map((h, i) => (
                  <th key={h} className={`py-3 px-4 text-xs font-bold uppercase tracking-wider ${i >= 3 ? "text-right" : "text-left"} ${i === 6 ? "text-center" : ""}`}
                    style={{ color: "#607080" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 30).map((r, i) => (
                <tr key={r.id || i} style={{ borderBottom: "1px solid #0A0F18", background: r.is_anomaly ? "#FF33660A" : "transparent" }}>
                  <td className="py-2.5 px-4 text-sm" style={{ color: "#708090" }}>{formatTimestamp(r.created_at)}</td>
                  <td className="py-2.5 px-4 text-sm font-bold" style={{ color: SENSOR_COLORS[r.sensor_type] || "#607080" }}>{r.sensor_type}</td>
                  <td className="py-2.5 px-4 text-sm" style={{ color: "#607080" }}>{sensorLabel(r.sensor_type)}</td>
                  <td className="py-2.5 px-4 text-right text-sm font-medium" style={{ color: "#BCC8D4" }}>{formatNumber(r.raw_value, 4)}</td>
                  <td className="py-2.5 px-4 text-right text-sm" style={{ color: "#506070" }}>{r.unit}</td>
                  <td className="py-2.5 px-4 text-right text-sm font-bold" style={{
                    color: r.anomaly_score >= 60 ? "#FF3366" : r.anomaly_score >= 30 ? "#FFAA00" : "#00FF88",
                  }}>{formatNumber(r.anomaly_score)}</td>
                  <td className="py-2.5 px-4 text-center text-sm font-bold" style={{
                    color: r.is_transmitted ? "#00FF88" : "#2A3A4D",
                  }}>{r.is_transmitted ? "İLETİLDİ" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
