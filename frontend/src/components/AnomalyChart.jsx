import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";
import { formatNumber } from "../utils/formatters";

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const accent = "#00F2FF";
  return (
    <div
      className="px-4 py-3.5 min-w-[180px]"
      style={{
        background: "rgba(6, 9, 16, 0.94)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        border: `1px solid ${accent}40`,
        boxShadow: `0 0 32px ${accent}18, 0 12px 40px rgba(0,0,0,0.55)`,
        fontFamily: '"JetBrains Mono", ui-monospace, monospace',
      }}
    >
      <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: accent, textShadow: `0 0 12px ${accent}40` }}>
        Anomali skoru
      </p>
      <p className="text-[11px] mb-2" style={{ color: "#607080" }}>
        {d.time}
      </p>
      <p
        className="font-bold text-xl tabular-nums leading-none mb-2"
        style={{ color: accent, textShadow: `0 0 16px ${accent}50` }}
      >
        {formatNumber(d.score)}
      </p>
      <p className="text-[11px]" style={{ color: "#506070" }}>
        SENSÖR{" "}
        <span className="font-semibold" style={{ color: "#BCC8D4" }}>
          {d.sensor}
        </span>
      </p>
    </div>
  );
}

export default function AnomalyChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="n-hud p-6">
        <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: "#607080" }}>ANOMALİ_SKORU_ZAMAN_SERİSİ</p>
        <div className="flex items-center justify-center h-60 text-sm" style={{ color: "#607080" }}>VERİ_BEKLENİYOR...</div>
      </div>
    );
  }

  return (
    <div className="n-hud p-6">
      <div className="flex items-center justify-between mb-5">
        <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>ANOMALİ_SKORU_ZAMAN_SERİSİ</p>
        <div className="flex gap-5 text-xs uppercase tracking-wide" style={{ color: "#708090" }}>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3" style={{ background: "#FF336660" }} /> ANOMALİ</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3" style={{ background: "#FFAA0040" }} /> ŞÜPHELİ</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3" style={{ background: "#00FF8830" }} /> NORMAL</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 28 }}>
          <defs>
            <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FF3366" stopOpacity={0.35} />
              <stop offset="40%" stopColor="#FFAA00" stopOpacity={0.1} />
              <stop offset="100%" stopColor="#00FF88" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#0D152020" />
          <XAxis
            dataKey="time"
            interval="preserveStartEnd"
            angle={-28}
            textAnchor="end"
            height={52}
            tick={{ fontSize: 9, fill: "#708090", fontFamily: "JetBrains Mono" }}
            axisLine={{ stroke: "#0D1520" }}
            tickLine={false}
          />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#708090", fontFamily: "JetBrains Mono" }} axisLine={{ stroke: "#0D1520" }} tickLine={false} />
          <Tooltip
            content={<ChartTooltip />}
            cursor={{ stroke: "#00F2FF30", strokeWidth: 1 }}
            wrapperStyle={{ outline: "none", zIndex: 50 }}
            allowEscapeViewBox={{ x: true, y: true }}
          />
          <ReferenceLine y={60} stroke="#FF336640" strokeDasharray="6 3" />
          <ReferenceLine y={30} stroke="#FFAA0025" strokeDasharray="6 3" />
          <Area type="monotone" dataKey="score" stroke="#00F2FF" strokeWidth={2} fill="url(#sg)" dot={false} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
