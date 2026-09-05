import { useState, useEffect, useMemo } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";
import { formatNumber, formatTimestamp, sensorLabel } from "../utils/formatters";

const SENSOR_COLORS = {
  TEMP: "#00F2FF", CH4: "#FF00FF", O2: "#00FF88", CO2: "#FFAA00",
  MOIST: "#7000FF", SPEC: "#FF3366", UV: "#FF8800", PRESS: "#00F2FF",
};

const SENSOR_INFO = {
  TEMP:  { range: "-80 — +20 °C", desc: "Mars yüzey ve atmosfer sıcaklığı. MSL görevinde REMS (Rover Environmental Monitoring Station) bu tür ölçümleri sağlar; veri setindeki kanallar MSL telemetrisine karşılık gelir.", unit: "°C" },
  CH4:   { range: "0 — 50 ppb", desc: "Metan konsantrasyonu. MSL’de SAM (Sample Analysis at Mars) gaz analizi yapar; Kaggle MSL kanalları bu bağlamda yorumlanır.", unit: "ppb" },
  O2:    { range: "0.1 — 0.2 %", desc: "Atmosferik oksijen seviyesi. Mars atmosferinde çok düşük konsantrasyonda bulunur.", unit: "%" },
  CO2:   { range: "95 — 96 %", desc: "Karbondioksit — Mars atmosferinin ana bileşeni. Mevsimsel değişimler gösterir.", unit: "%" },
  MOIST: { range: "0 — 100 %", desc: "Nem / su buharı ile ilişkili sinyal. MSL REMS nem ölçümleri ile uyumlu senaryo; kanal veri setinden türetilmiştir.", unit: "%" },
  SPEC:  { range: "0 — 1000 nm", desc: "Spektral yoğunluk (normalize seri). MSL’de ChemCam vb. spektroskopik ölçümler vardır; buradaki SPEC kanalları veri setindeki MSL kanallarına karşılık gelir (Perseverance PIXL/SHERLOC değil).", unit: "nm" },
  UV:    { range: "0 — 500 mW/m²", desc: "Ultraviyole radyasyon. REMS UV sensörü ile uyumlu senaryo; Mars yüzeyindeki UV Dünya’dan yüksektir.", unit: "mW/m²" },
  PRESS: { range: "600 — 800 Pa", desc: "Atmosferik basınç. REMS basınç ölçümleri; Mars’ta Dünya’nın yaklaşık %1’i düzeyinde.", unit: "Pa" },
};

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="p-3" style={{ background: "#080C14", border: "1px solid #1A2535" }}>
      <p className="text-xs" style={{ color: "#708090" }}>{d.time}</p>
      <p className="font-bold text-base mt-0.5" style={{ color: "#00F2FF" }}>{formatNumber(d.value, 4)}</p>
      <p className="text-xs mt-0.5" style={{ color: "#708090" }}>Skor: <span style={{ color: d.score >= 60 ? "#FF3366" : d.score >= 30 ? "#FFAA00" : "#00FF88" }}>{formatNumber(d.score)}</span></p>
    </div>
  );
}

const CHART_POINTS = 50;

export default function SensorDetail({ readings, readingsByType = {}, anomalies }) {
  const [selected, setSelected] = useState("TEMP");
  const [sensorStats, setSensorStats] = useState(null);
  const [apiSeries, setApiSeries] = useState([]);
  const [seriesLoading, setSeriesLoading] = useState(false);
  const [apiAnomalies, setApiAnomalies] = useState([]);

  useEffect(() => {
    fetch("/api/sensor-data/stats").then(r => r.json()).then(setSensorStats).catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setSeriesLoading(true);
    const q = new URLSearchParams({ sensor_type: selected, limit: "200" });
    fetch(`/api/sensor-data?${q}`)
      .then(r => (r.ok ? r.json() : []))
      .then(rows => {
        if (!cancelled) setApiSeries(Array.isArray(rows) ? rows : []);
      })
      .catch(() => {
        if (!cancelled) setApiSeries([]);
      })
      .finally(() => {
        if (!cancelled) setSeriesLoading(false);
      });
    return () => { cancelled = true; };
  }, [selected]);

  useEffect(() => {
    fetch("/api/anomalies?limit=400")
      .then(r => (r.ok ? r.json() : []))
      .then(rows => setApiAnomalies(Array.isArray(rows) ? rows : []))
      .catch(() => setApiAnomalies([]));
  }, []);

  const sensorReadings = useMemo(() => {
    const fromApi = apiSeries;
    const fromTyped = (readingsByType && readingsByType[selected]) || [];
    const fromMixed = readings.filter(r => r.sensor_type === selected);
    const byId = new Map();
    for (const r of fromApi) {
      if (r?.id) byId.set(String(r.id), r);
    }
    for (const r of fromTyped) {
      if (r?.id) byId.set(String(r.id), r);
    }
    for (const r of fromMixed) {
      if (r?.id) byId.set(String(r.id), r);
    }
    return Array.from(byId.values())
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, CHART_POINTS);
  }, [apiSeries, readings, readingsByType, selected]);

  const chartData = useMemo(() =>
    [...sensorReadings].reverse().map(r => ({
      time: formatTimestamp(r.created_at),
      value: r.raw_value,
      score: r.anomaly_score,
    })),
  [sensorReadings]);

  const mergedAnomalies = useMemo(() => {
    const byId = new Map();
    for (const a of apiAnomalies) {
      if (a?.id) byId.set(String(a.id), a);
    }
    for (const a of anomalies) {
      if (a?.id) byId.set(String(a.id), a);
    }
    return Array.from(byId.values());
  }, [apiAnomalies, anomalies]);

  // Anomaliyi sensöre bağlarken önce API'nin verdiği sensor_type kullanılır.
  // Eski kayıtlarda bu alan yoksa okuma kimliği üzerinden eşleştirilir; metin
  // araması yalnızca son çare olarak kalır (yanlış eşleşme üretebiliyordu).
  const readingSensorById = useMemo(() => {
    const map = new Map();
    for (const r of readings) {
      if (r?.id) map.set(String(r.id), r.sensor_type);
    }
    for (const list of Object.values(readingsByType || {})) {
      for (const r of list || []) {
        if (r?.id) map.set(String(r.id), r.sensor_type);
      }
    }
    return map;
  }, [readings, readingsByType]);

  const sensorAnomalies = useMemo(() =>
    mergedAnomalies
      .filter(a => {
        if (a.sensor_type) return a.sensor_type === selected;
        const fromReading = readingSensorById.get(String(a.reading_id));
        if (fromReading) return fromReading === selected;
        const desc = a.description || "";
        return desc.includes(selected) || desc.includes(sensorLabel(selected));
      })
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 15),
  [mergedAnomalies, selected, readingSensorById]);

  const currentStats = sensorStats?.find(s => s.sensor_type === selected);
  const info = SENSOR_INFO[selected] || {};
  const color = SENSOR_COLORS[selected] || "#00F2FF";

  const statsBars = sensorStats?.map(s => ({
    name: s.sensor_type,
    anomaly_rate: (s.anomaly_rate * 100),
    color: SENSOR_COLORS[s.sensor_type] || "#506070",
  })) || [];

  return (
    <div className="space-y-5">
      {/* Sensor selector */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>SENSÖR_DETAY</p>
          <p className="text-xs mt-1 max-w-xl leading-relaxed" style={{ color: "#607080" }}>
            Grafik değerleri [-1, 1] normalize telemetrıdır (fiziksel °C / ppb / Pa değil). Sağdaki aralık yalnızca enstrüman bağlamıdır. Son {CHART_POINTS} okuma veritabanından yüklenir ve WebSocket ile güncellenir.
          </p>
        </div>
        <div className="flex gap-1">
          {Object.keys(SENSOR_INFO).map(s => (
            <button key={s} onClick={() => setSelected(s)}
              className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-all"
              style={{
                background: selected === s ? `${SENSOR_COLORS[s]}15` : "transparent",
                border: `1px solid ${selected === s ? `${SENSOR_COLORS[s]}50` : "#0D1520"}`,
                color: selected === s ? SENSOR_COLORS[s] : "#506070",
                textShadow: selected === s ? `0 0 8px ${SENSOR_COLORS[s]}30` : "none",
              }}>{s}</button>
          ))}
        </div>
      </div>

      {/* Sensor info card */}
      <div className="n-hud p-5" style={{ borderColor: `${color}20` }}>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xl font-extrabold" style={{ color, textShadow: `0 0 12px ${color}40` }}>{selected}</span>
              <span className="text-sm font-medium" style={{ color: "#8899AA" }}>{sensorLabel(selected)}</span>
            </div>
            <p className="text-sm leading-relaxed max-w-2xl" style={{ color: "#708090" }}>{info.desc}</p>
          </div>
          <div className="text-right shrink-0 ml-6">
            <p className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: "#506070" }}>FİZİKSEL (REF.)</p>
            <p className="text-sm font-bold" style={{ color: "#8899AA" }}>{info.range}</p>
            <p className="text-[10px] mt-1" style={{ color: "#506070" }}>grafik: normalize</p>
          </div>
        </div>
        {currentStats && (
          <div className="grid grid-cols-4 gap-4 mt-5 pt-4" style={{ borderTop: "1px solid #0D1520" }}>
            {[
              { l: "ORTALAMA", v: formatNumber(currentStats.mean, 4), c: color },
              { l: "STD_SAPMA", v: formatNumber(currentStats.std, 4), c: "#8899AA" },
              { l: "ANOMALİ_ORANI", v: `%${formatNumber(currentStats.anomaly_rate * 100)}`, c: currentStats.anomaly_rate > 0.1 ? "#FF3366" : "#00FF88" },
              { l: "TOPLAM_OKUMA", v: currentStats.count.toLocaleString("tr-TR"), c: "#8899AA" },
            ].map(m => (
              <div key={m.l}>
                <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>{m.l}</p>
                <p className="text-lg font-extrabold mt-1" style={{ color: m.c }}>{m.v}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Time series chart */}
      <div className="n-hud p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>
            {selected}_ZAMAN_SERİSİ
          </p>
          <span className="text-[10px] uppercase tracking-widest" style={{ color: "#506070" }}>
            SON_{CHART_POINTS}_NOKTA · DB + sensör_tamponu + WS
          </span>
        </div>
        {chartData.length === 0 && seriesLoading ? (
          <div className="flex items-center justify-center h-48 text-sm" style={{ color: "#506070" }}>SERİ_YÜKLENİYOR...</div>
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-sm" style={{ color: "#506070" }}>VERİ_BEKLENİYOR...</div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <defs>
                <linearGradient id={`grad-${selected}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={color} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#0D152020" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#708090", fontFamily: "JetBrains Mono" }} axisLine={{ stroke: "#0D1520" }} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#708090", fontFamily: "JetBrains Mono" }} axisLine={{ stroke: "#0D1520" }} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Area type="monotone" dataKey="value" stroke={color} strokeWidth={2} fill={`url(#grad-${selected})`} dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* Anomaly rate comparison */}
        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: "#607080" }}>SENSÖR_ANOMALİ_ORANI_KARŞILAŞTIRMA</p>
          {statsBars.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={statsBars} margin={{ left: 0, right: 10 }}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#708090", fontFamily: "JetBrains Mono" }} axisLine={{ stroke: "#0D1520" }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#506070", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <Bar dataKey="anomaly_rate" radius={[2, 2, 0, 0]} barSize={24}>
                  {statsBars.map((e, i) => <Cell key={i} fill={e.name === selected ? e.color : "#1A2535"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-sm" style={{ color: "#506070" }}>İSTATİSTİK_HESAPLANIYOR...</div>
          )}
        </div>

        {/* Anomaly history */}
        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: "#607080" }}>
            {selected}_ANOMALİ_GEÇMİŞİ
          </p>
          {sensorAnomalies.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-sm" style={{ color: "#506070" }}>
              BU_SENSÖR_İÇİN_ANOMALİ_YOK
            </div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto">
              {sensorAnomalies.map(a => (
                <div key={a.id} className="px-3 py-2" style={{ background: "#050810", border: "1px solid #0D1520" }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold uppercase" style={{ color }}>{a.anomaly_type}</span>
                    <span className="text-xs" style={{ color: "#506070" }}>{formatTimestamp(a.created_at)}</span>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: "#708090" }}>{a.description?.slice(0, 120)}...</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
