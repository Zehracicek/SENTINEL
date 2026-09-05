import { useEffect, useMemo, useState } from "react";
import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Area,
  AreaChart,
} from "recharts";

export default function OrbiterRelay({ orbiterStats, stats }) {
  const [logs, setLogs] = useState([]);

  const o = useMemo(
    () => ({ ...(stats?.orbiter_stats || {}), ...(orbiterStats || {}) }),
    [stats?.orbiter_stats, orbiterStats]
  );

  useEffect(() => {
    let cancel = false;
    const load = () => {
      fetch("/api/orbiter-log?limit=50")
        .then((r) => (r.ok ? r.json() : []))
        .then((rows) => {
          if (!cancel && Array.isArray(rows)) setLogs(rows);
        })
        .catch(() => {});
    };
    load();
    const id = setInterval(load, 25000);
    return () => {
      cancel = true;
      clearInterval(id);
    };
  }, [o?.last_pass_id]);

  const chartData = [...logs]
    .reverse()
    .map((row, i) => {
      const ms = Number(row.relay_latency_ms);
      const ts = row.created_at ? new Date(row.created_at) : null;
      return {
        i,
        ms: Number.isFinite(ms) ? ms : 0,
        t:
          ts && !Number.isNaN(ts.getTime())
            ? ts.toLocaleTimeString("tr-TR", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })
            : "—",
      };
    });

  const dropPct = o?.drop_rate != null ? (o.drop_rate * 100).toFixed(1) : "—";
  const winRem = o?.window_remaining_sec;
  const buf = o?.buffer_pending ?? "—";

  const pipeline = [
    { step: "01", title: "MARS_EDGE", desc: "Skor ≥ eşik uplink uygun paketler kuyruğa alınır." },
    { step: "02", title: "DSN_UPLINK", desc: "Deep Space Network üzerinden Mars→Dünya bağlantısı (simüle)." },
    { step: "03", title: "ORBITER_EDGE2", desc: `${o?.window_seconds ?? 30} sn hareketli pencere; tamponda biriken paketler toplanır.` },
    { step: "04", title: "İKİNCİL_FİLTRE", desc: "Skor < 40 olanlar düşürülür; iletilenler bir sonraki aşamaya gider." },
    { step: "05", title: "RELAY_LOG", desc: "Her pencere sonunda gecikme ve hacim istatistikleri kalıcı loga yazılır." },
  ];

  return (
    <div className="w-full space-y-8">
      <header className="space-y-2">
        <p className="text-[10px] font-bold uppercase tracking-[0.25em]" style={{ color: "#00F2FF" }}>
          ORBITER · UÇ2 RÖLESİ
        </p>
        <h2 className="text-2xl font-black uppercase tracking-wide" style={{ color: "#E8EEF4" }}>
          Yörünge Aktarım Katmanı
        </h2>
        <p className="text-sm max-w-4xl leading-relaxed" style={{ color: "#708090" }}>
          Bu panel, Mars yüzeyinden gelen önceliklendirilmiş telemetrinin yer istasyonuna ikinci bir “edge” üzerinden
          geçişini izler. Gerçek sistemlerde MEO/GEO röle veya yakın yörünge varlıkları benzer tamponlama ve
          yeniden planlama sağlar; burada süreç deterministik simülasyon + kalıcı relay günlüğü ile modellenir.
        </p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {[
          { l: "ALINAN_TOPLAM", v: o?.packets_received ?? "—", c: "#00F2FF", sub: "orbiter girişi" },
          { l: "İLETİLEN", v: o?.packets_forwarded ?? "—", c: "#FF00FF", sub: "pencere çıkışı" },
          { l: "İKİNCİL_DROP", v: o?.packets_dropped_secondary ?? "—", c: "#FFAA00", sub: "skor < 40" },
          { l: "DROP_ORANI", v: `${dropPct}%`, c: "#FF3366", sub: "alınan / düşen" },
          { l: "ORT_GECİKME_MS", v: o?.avg_relay_latency_ms ?? "—", c: "#00FF88", sub: "simüle RTT" },
          { l: "TAMPON", v: buf, c: "#8899AA", sub: "aktif pencere" },
        ].map((x) => (
          <div key={x.l} className="n-hud p-3 rounded-lg border" style={{ borderColor: `${x.c}28` }}>
            <p className="text-[9px] font-bold uppercase tracking-wider mb-0.5" style={{ color: "#506070" }}>
              {x.l}
            </p>
            <p className="text-xl font-extrabold tabular-nums leading-tight" style={{ color: x.c }}>
              {x.v}
            </p>
            <p className="text-[9px] mt-1 uppercase" style={{ color: "#3A4A5C" }}>
              {x.sub}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="n-panel p-5 rounded-lg border" style={{ borderColor: "#0D1520" }}>
          <p className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color: "#607080" }}>
            Pencere durumu
          </p>
          <div className="grid grid-cols-2 gap-4 mt-3 font-mono text-sm" style={{ color: "#99AAB8" }}>
            <div>
              <p style={{ color: "#506070" }} className="text-[10px] uppercase mb-1">
                Pencere süresi
              </p>
              <p className="text-lg font-bold" style={{ color: "#00F2FF" }}>
                {o?.window_seconds ?? 30} sn
              </p>
            </div>
            <div>
              <p style={{ color: "#506070" }} className="text-[10px] uppercase mb-1">
                Kalan süre
              </p>
              <p className="text-lg font-bold" style={{ color: winRem != null ? "#00FF88" : "#506070" }}>
                {winRem != null ? `${winRem} sn` : "—"}
              </p>
            </div>
            <div className="col-span-2">
              <p style={{ color: "#506070" }} className="text-[10px] uppercase mb-1">
                Son geçiş kimliği
              </p>
              <p className="text-xs break-all" style={{ color: "#FF00FF" }}>
                {o?.last_pass_id || "—"}
              </p>
            </div>
          </div>
        </div>

        <div className="n-panel p-5 rounded-lg border" style={{ borderColor: "#0D1520" }}>
          <p className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "#607080" }}>
            Veri akışı özeti
          </p>
          <ul className="space-y-3">
            {pipeline.map((p) => (
              <li key={p.step} className="flex gap-3">
                <span
                  className="shrink-0 w-8 h-8 flex items-center justify-center rounded text-[10px] font-black"
                  style={{ background: "#00F2FF18", color: "#00F2FF", border: "1px solid #00F2FF33" }}
                >
                  {p.step}
                </span>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide" style={{ color: "#99AAB8" }}>
                    {p.title}
                  </p>
                  <p className="text-[11px] mt-0.5 leading-snug" style={{ color: "#607080" }}>
                    {p.desc}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="n-panel p-4 rounded-lg border w-full" style={{ borderColor: "#0D1520", minHeight: 360 }}>
        <div className="flex justify-between items-center mb-2">
          <p className="text-xs font-bold uppercase tracking-wider" style={{ color: "#607080" }}>
            Röle gecikmesi (ms)
          </p>
          <span className="text-[10px] font-mono" style={{ color: "#506070" }}>
            Son {chartData.length} geçiş
          </span>
        </div>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="orbLat" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00F2FF" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#00F2FF" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#0D1520" strokeDasharray="3 3" />
              <XAxis dataKey="t" tick={{ fill: "#506070", fontSize: 9 }} />
              <YAxis tick={{ fill: "#506070", fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: "#080C14", border: "1px solid #0D1520", color: "#99AAB8" }}
              />
              <Area type="monotone" dataKey="ms" stroke="#00F2FF" fill="url(#orbLat)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg border overflow-hidden" style={{ background: "#060910", borderColor: "#0D1520" }}>
        <div
          className="px-4 py-2.5 border-b flex justify-between items-center"
          style={{ borderColor: "#0D1520" }}
        >
          <span className="text-xs font-bold uppercase" style={{ color: "#607080" }}>
            ORBITER_RÖLE_GÜNLÜĞÜ
          </span>
          <span className="text-[10px] font-mono" style={{ color: "#506070" }}>
            PostgreSQL · orbiter_relay_log
          </span>
        </div>
        <div className="overflow-x-auto max-h-80 overflow-y-auto">
          <table className="w-full text-xs font-mono">
            <thead style={{ color: "#506070" }}>
              <tr className="text-left border-b sticky top-0" style={{ borderColor: "#0D1520", background: "#060910" }}>
                <th className="p-2.5">Zaman (UTC)</th>
                <th className="p-2.5">pass_id</th>
                <th className="p-2.5">Alınan</th>
                <th className="p-2.5">İletilen</th>
                <th className="p-2.5">Gecikme ms</th>
              </tr>
            </thead>
            <tbody style={{ color: "#99AAB8" }}>
              {logs.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-6 text-center" style={{ color: "#506070" }}>
                    Henüz röle günlük kaydı yok — orbiter boşaltma döngüsü çalıştıkça dolar.
                  </td>
                </tr>
              )}
              {logs.slice(0, 40).map((row) => (
                <tr key={row.id} className="border-b hover:bg-white/[0.02]" style={{ borderColor: "#0D1520" }}>
                  <td className="p-2.5 whitespace-nowrap">{new Date(row.created_at).toLocaleString("tr-TR")}</td>
                  <td className="p-2.5 max-w-[140px] truncate" title={row.pass_id}>
                    {row.pass_id}
                  </td>
                  <td className="p-2.5 tabular-nums">{row.packets_received}</td>
                  <td className="p-2.5 tabular-nums">{row.packets_forwarded}</td>
                  <td className="p-2.5 tabular-nums" style={{ color: "#00F2FF" }}>
                    {row.relay_latency_ms}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
