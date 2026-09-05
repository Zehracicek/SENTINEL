import { formatNumber, severityColor } from "../utils/formatters";

function Card({ label, value, sub, color }) {
  return (
    <div className="n-hud p-5" style={{ background: "linear-gradient(135deg, #080C14, #060910)", borderColor: `${color}15` }}>
      <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>{label}</p>
      <p className="text-4xl font-extrabold tabular-nums tracking-tight" style={{ color, textShadow: `0 0 12px ${color}40` }}>{value}</p>
      {sub && <p className="text-xs mt-2 uppercase tracking-wide" style={{ color: "#607080" }}>{sub}</p>}
      <div className="mt-4 h-px" style={{ background: `linear-gradient(to right, ${color}30, transparent 70%)` }} />
    </div>
  );
}

export default function MetricCards({ stats }) {
  if (!stats) return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[1,2,3,4].map(i => <div key={i} className="n-panel h-36 animate-pulse" />)}
    </div>
  );

  const sev = stats.highest_severity;
  const sevS = severityColor(sev);

  const rs = stats.river_stats;
  const es = stats.energy_stats;
  const rls = stats.rl_stats;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card label="TOPLAM_ANOMALİ" value={stats.total_anomalies ?? 0} sub="Tespit edilen anomali sayısı" color="#FF3366" />
        <Card label="BANT_TASARRUFU" value={`%${formatNumber(stats.bandwidth_saved_percent)}`} sub="Uçta işlemle elde edilen bant genişliği kazancı" color="#00FF88" />
        <Card label="İŞLENEN_PAKET" value={(stats.total_packets ?? stats.total_readings ?? 0).toLocaleString("tr-TR")} sub="Toplam sensör okuması" color="#00F2FF" />
        <div className="n-hud p-5" style={{ background: "linear-gradient(135deg, #080C14, #060910)" }}>
          <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>EN_YÜKSEK_ÖNCELİK</p>
          {sev ? (
            <span className="inline-block px-4 py-2 text-sm font-bold uppercase tracking-wider mt-1" style={{
              backgroundColor: sevS.bg, color: sevS.text, border: `1px solid ${sevS.border}`, textShadow: `0 0 8px ${sevS.text}40`,
            }}>{sev}</span>
          ) : <p className="text-4xl font-extrabold" style={{ color: "#2A3A4D" }}>—</p>}
          <p className="text-xs mt-2 uppercase tracking-wide" style={{ color: "#607080" }}>Kayıtlar arası en yüksek şiddet (eşitlikte en yeni)</p>
          <div className="mt-4 h-px" style={{ background: "linear-gradient(to right, #7000FF30, transparent 70%)" }} />
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card
          label="ÇEVRİMİÇİ_MODEL (RIVER)"
          value={rs?.n_samples_seen ?? "—"}
          sub={`sürüm ${rs?.model_version ?? "—"} · River HalfSpaceTrees (çevrimiçi ağaçlar)`}
          color="#7000FF"
        />
        <Card
          label="ENERJİ_BATARYA"
          value={es != null ? `%${formatNumber(es.batarya_level)}` : "—"}
          sub={es != null ? `CPU ${formatNumber(es.cpu_load)}% · eşik ${es.aktif_esik} · zlib ${es.zlib_level}` : "—"}
          color="#FFB800"
        />
        <Card
          label="PEKIŞTİRMELİ_AJAN"
          value={rls?.total_reward ?? "—"}
          sub={rls != null ? `ε ${rls.epsilon} · adım ${rls.steps} · Q-tablo ${rls.q_table_size}` : "—"}
          color="#00FF88"
        />
      </div>
    </div>
  );
}
