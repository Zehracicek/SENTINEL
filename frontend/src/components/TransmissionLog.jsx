import { formatNumber, formatBytes } from "../utils/formatters";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from "recharts";

function CircularGauge({ percent, label, color }) {
  const r = 40, circ = 2 * Math.PI * r;
  const offset = circ - (percent / 100) * circ;
  return (
    <svg width="100" height="100" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r={r} fill="none" stroke="#0D1520" strokeWidth="5" />
      <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="5"
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="butt"
        transform="rotate(-90 50 50)" style={{ filter: `drop-shadow(0 0 6px ${color}50)` }} />
      <text x="50" y="47" textAnchor="middle" fill={color} fontSize="16" fontWeight="800" fontFamily="JetBrains Mono">
        %{formatNumber(percent, 0)}
      </text>
      <text x="50" y="62" textAnchor="middle" fill="#506070" fontSize="7" fontWeight="600" fontFamily="JetBrains Mono">{label}</text>
    </svg>
  );
}

export default function TransmissionLog({ stats }) {
  if (!stats) return <div className="n-hud h-96 animate-pulse" />;

  const total = stats.total_packets ?? stats.total_readings ?? 0;
  const tx = Math.min(stats.transmitted_packets ?? 0, Math.max(0, total));
  const dropped = Math.max(0, total - tx);
  const savedPct = Math.min(100, Math.max(0, Number(stats.bandwidth_saved_percent) || 0));
  const bytesSaved = stats.total_bytes_saved ?? 0;
  const ratio = Math.min(1, Math.max(0, Number(stats.compression_ratio) || 0));
  const deflateRatio = Math.min(1, Math.max(0, Number(stats.payload_deflate_ratio) || 0));
  const deflateSavings = Math.min(100, Math.max(0, Number(stats.payload_deflate_savings_percent) || 0));

  const dsnData = [
    { name: "Goldstone DSS-14", konum: "California, ABD", bant: "X-Band", hiz: "~3 kbps", durum: true },
    { name: "Canberra DSS-43", konum: "Avustralya", bant: "UHF", hiz: "~2 Mbps", durum: false },
    { name: "Madrid DSS-63", konum: "İspanya", bant: "X-Band", hiz: "~3 kbps", durum: true },
  ];

  const pieData = [
    { name: "İletilen", value: tx, fill: "#FF00FF" },
    { name: "Filtrelenen", value: dropped, fill: "#1A2535" },
  ];

  return (
    <div className="space-y-5">
      <div>
        <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>İLETİM_ANALİZİ</p>
        <p className="text-sm mt-1" style={{ color: "#708090" }}>DSN iletim durumu, bant genişliği analizi ve paket istatistikleri</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { l: "TOPLAM PAKET", v: total.toLocaleString("tr-TR"), c: "#00F2FF" },
          { l: "İLETİLEN", v: tx.toLocaleString("tr-TR"), c: "#FF00FF" },
          { l: "FİLTRELENEN", v: dropped.toLocaleString("tr-TR"), c: "#FFAA00" },
          { l: "TASARRUF", v: formatBytes(bytesSaved), c: "#00FF88" },
        ].map(m => (
          <div key={m.l} className="n-hud p-5" style={{ background: "linear-gradient(135deg, #080C14, #060910)" }}>
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>{m.l}</p>
            <p className="text-2xl font-extrabold mt-2" style={{ color: m.c, textShadow: `0 0 10px ${m.c}30` }}>{m.v}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Gauges */}
        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: "#607080" }}>BANT_VERİMLİLİĞİ</p>
          <div className="flex justify-around items-center">
            <CircularGauge percent={savedPct} label="TASARRUF" color="#00FF88" />
            <CircularGauge percent={ratio * 100} label="İLETİM" color="#FF00FF" />
          </div>
          <div className="mt-4 pt-3 space-y-2" style={{ borderTop: "1px solid #0D1520" }}>
            <div className="flex justify-between px-2">
              <span className="text-xs" style={{ color: "#506070" }}>İletim Oranı (paket)</span>
              <span className="text-sm font-bold" style={{ color: "#8899AA" }}>{formatNumber(ratio, 4)}</span>
            </div>
            <div className="flex justify-between px-2">
              <span className="text-xs" style={{ color: "#506070" }}>Delta+DEFLATE (sıkıştırılmış / ham)</span>
              <span className="text-sm font-bold" style={{ color: "#00FF88" }}>{deflateRatio > 0 ? formatNumber(deflateRatio, 4) : "—"}</span>
            </div>
            <div className="flex justify-between px-2">
              <span className="text-xs" style={{ color: "#506070" }}>Yük Sıkıştırma Tasarrufu</span>
              <span className="text-sm font-bold" style={{ color: "#00F2FF" }}>{deflateSavings > 0 ? `%${formatNumber(deflateSavings, 1)}` : "—"}</span>
            </div>
            <div className="flex justify-between px-2">
              <span className="text-xs" style={{ color: "#506070" }}>Paket Başı Boyut</span>
              <span className="text-sm font-bold" style={{ color: "#8899AA" }}>256 byte</span>
            </div>
            <div className="flex justify-between px-2">
              <span className="text-xs" style={{ color: "#506070" }}>Toplam Ham Veri</span>
              <span className="text-sm font-bold" style={{ color: "#8899AA" }}>{formatBytes(total * 256)}</span>
            </div>
          </div>
        </div>

        {/* Pie */}
        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: "#607080" }}>PAKET_DAĞILIMI</p>
          {total === 0 ? (
            <div className="flex flex-col items-center justify-center h-[180px] text-sm" style={{ color: "#506070" }}>
              Henüz paket yok — simülasyon başladıkça dolar.
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                    {pieData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-6 mt-2">
                <span className="flex items-center gap-2 text-xs" style={{ color: "#708090" }}>
                  <span className="w-3 h-3" style={{ background: "#FF00FF" }} /> İletilen ({tx})
                </span>
                <span className="flex items-center gap-2 text-xs" style={{ color: "#708090" }}>
                  <span className="w-3 h-3" style={{ background: "#1A2535" }} /> Filtrelenen ({dropped})
                </span>
              </div>
            </>
          )}
        </div>

        {/* DSN Stations */}
        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: "#607080" }}>DSN_İSTASYONLARI</p>
          <div className="space-y-2">
            {dsnData.map(d => (
              <div key={d.name} className="p-3" style={{ background: "#050810", border: "1px solid #0D1520" }}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-bold" style={{ color: "#BCC8D4" }}>{d.name}</span>
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.durum ? "#00FF88" : "#2A3A4D", boxShadow: d.durum ? "0 0 6px #00FF8860" : "none" }} />
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div><span style={{ color: "#506070" }}>Konum: </span><span style={{ color: "#708090" }}>{d.konum}</span></div>
                  <div><span style={{ color: "#506070" }}>Bant: </span><span style={{ color: "#708090" }}>{d.bant}</span></div>
                  <div><span style={{ color: "#506070" }}>Hız: </span><span style={{ color: "#00F2FF" }}>{d.hiz}</span></div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-3 space-y-1.5" style={{ borderTop: "1px solid #0D1520" }}>
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>İLETİM_BİLGİSİ</p>
            <p className="text-xs" style={{ color: "#607080" }}>Gecikme: <span style={{ color: "#FFAA00" }}>4-24 dakika</span> (tek yön)</p>
            <p className="text-xs" style={{ color: "#607080" }}>Günlük kapasite: <span style={{ color: "#8899AA" }}>~1 Gbit</span></p>
            <p className="text-xs" style={{ color: "#607080" }}>Geçiş sayısı: <span style={{ color: "#8899AA" }}>4-5 / sol</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}
