import { formatNumber, formatBytes } from "../utils/formatters";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

function CircularGauge({ percent }) {
  const r = 54, circ = 2 * Math.PI * r;
  const offset = circ - (percent / 100) * circ;
  const color = percent > 70 ? "#00FF88" : percent > 40 ? "#FFAA00" : "#FF3366";
  return (
    <svg width="150" height="150" viewBox="0 0 150 150">
      <circle cx="75" cy="75" r={r} fill="none" stroke="#0D1520" strokeWidth="7" />
      <circle cx="75" cy="75" r={r} fill="none" stroke={color} strokeWidth="7"
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="butt"
        transform="rotate(-90 75 75)" className="transition-all duration-1000"
        style={{ filter: `drop-shadow(0 0 10px ${color}50)` }} />
      <text x="75" y="68" textAnchor="middle" fill={color} fontSize="22" fontWeight="800" fontFamily="JetBrains Mono">%{formatNumber(percent, 1)}</text>
      <text x="75" y="88" textAnchor="middle" fill="#607080" fontSize="9" fontWeight="600" fontFamily="JetBrains Mono" letterSpacing="0.15em">TASARRUF_ORANI</text>
    </svg>
  );
}

function ChartTip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const v = payload[0].value;
  const n = Number(v);
  const shown = Number.isFinite(n) ? n.toLocaleString("tr-TR") : "—";
  return (
    <div className="p-2 text-xs" style={{ background: "#080C14", border: "1px solid #1A2535" }}>
      <span style={{ color: "#99AAB8" }}>{payload[0].payload.name}: </span>
      <span className="font-bold" style={{ color: "#00F2FF" }}>{shown}</span>
    </div>
  );
}

export default function BandwidthGauge({ stats }) {
  if (!stats) return <div className="n-hud h-72 animate-pulse" />;
  const total = stats.total_packets ?? stats.total_readings ?? 0;
  const tx = Math.min(stats.transmitted_packets ?? 0, Math.max(0, total));
  const savedPct = Math.min(100, Math.max(0, Number(stats.bandwidth_saved_percent) || 0));
  const bytesSaved = stats.total_bytes_saved ?? 0;
  const barData = [
    { name: "HAM_VERİ", value: total, color: "#1A2535" },
    { name: "GÖNDERİLEN", value: tx, color: "#FF00FF" },
  ];

  return (
    <div className="n-hud p-6">
      <p className="text-xs font-bold uppercase tracking-widest mb-5" style={{ color: "#607080" }}>BANT_GENİŞLİĞİ_ANALİZİ</p>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
        <div className="flex justify-center"><CircularGauge percent={savedPct} /></div>
        <div>
          <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>HAM_VS_GÖNDERİLEN</p>
          <ResponsiveContainer width="100%" height={110}>
            <BarChart data={barData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <XAxis type="number" tick={{ fontSize: 10, fill: "#607080", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: "#8899AA", fontFamily: "JetBrains Mono" }} width={100} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTip />} cursor={{ fill: "#0D152020" }} />
              <Bar dataKey="value" radius={[0, 3, 3, 0]} barSize={18}>
                {barData.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-5 text-center">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: "#607080" }}>TOPLAM_TASARRUF</p>
            <p className="text-2xl font-extrabold text-glow-green" style={{ color: "#00FF88" }}>{formatBytes(bytesSaved)}</p>
          </div>
          <div className="h-px" style={{ background: "#0D1520" }} />
          <div>
            <p className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: "#607080" }}>FİLTRELENEN</p>
            <p className="text-xl font-bold" style={{ color: "#99AAB8" }}>{Math.max(0, total - tx).toLocaleString("tr-TR")} <span className="text-xs" style={{ color: "#607080" }}>PAKET</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}
