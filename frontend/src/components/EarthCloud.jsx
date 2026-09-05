import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  BarChart,
  Bar,
} from "recharts";

export default function EarthCloud({ modelUpdates, rlRewardSeries, stats }) {
  const [rows, setRows] = useState([]);

  const ecs = stats?.earth_cloud_state;
  const orb = stats?.orbiter_stats;

  useEffect(() => {
    let cancel = false;
    fetch("/api/model-updates?limit=40")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (!cancel && Array.isArray(data)) setRows(data);
      })
      .catch(() => {});
    return () => {
      cancel = true;
    };
  }, [modelUpdates?.[0]?.federated_round]);

  const merged = modelUpdates?.length ? modelUpdates : rows;
  const timeline = [...merged]
    .filter(
      (m) =>
        m.threshold_suggestion != null &&
        Number.isFinite(Number(m.threshold_suggestion))
    )
    .slice(0, 24)
    .reverse()
    .map((m, i) => ({
      i,
      round: m.federated_round ?? m.model_version,
      thr: Number(m.threshold_suggestion),
      label: String(m.federated_round ?? i),
    }));

  const rewardChart = (rlRewardSeries || [])
    .filter((p) => p != null && Number.isFinite(Number(p.reward)))
    .map((p, i) => ({
      i,
      reward: Number(p.reward),
      t: (() => {
        const d = p.t ? new Date(p.t) : null;
        return d && !Number.isNaN(d.getTime())
          ? d.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
          : "—";
      })(),
    }));

  const lastRound = merged[0]?.federated_round ?? stats?.rl_stats?.steps ?? "—";
  const batchesLeft = ecs?.batches_until_cloud_sync;
  const everyN = ecs?.cloud_sync_every_n_batches ?? 20;

  const fedSteps = useMemo(
    () => [
      {
        k: "A",
        t: "Orbiter rölesi",
        d: `Her ${everyN} röle partisi sonrası tetiklenir; şu an ${ecs?.orbiter_batches_since_cloud ?? "—"}/${everyN} sayaç.`,
      },
      {
        k: "B",
        t: "Yer istasyonu istatistiği",
        d: "Precision/recall (öncelik: Hundman dizi metriği) okunur; düşük precision eşiği yükseltir, düşük recall düşürür (40–70).",
      },
      {
        k: "C",
        t: "model_updates kaydı",
        d: "Öneri ve model sürümü kalıcı tabloya yazılır; WebSocket ile model_update olayı yayınlanır.",
      },
      {
        k: "D",
        t: "Pekiştirmeli geri besleme",
        d: "Epsilon ve Q-tablo, Dünya eşik önerisiyle güncellenir (kapalı döngü simülasyonu).",
      },
    ],
    [everyN, ecs?.orbiter_batches_since_cloud]
  );

  return (
    <div className="w-full space-y-8">
      <header className="space-y-2">
        <p className="text-[10px] font-bold uppercase tracking-[0.25em]" style={{ color: "#FF00FF" }}>
          YER İSTASYONU · EŞİK GERİ BİLDİRİMİ
        </p>
        <h2 className="text-2xl font-black uppercase tracking-wide" style={{ color: "#E8EEF4" }}>
          Dünya Bulutu & Kapalı Döngü Politikası
        </h2>
        <p className="text-sm max-w-4xl leading-relaxed" style={{ color: "#708090" }}>
          Bu modül, yer istasyonunun <strong style={{ color: "#99AAB8" }}>gecikmeli eşik önerisini</strong> modeller.
          Ağırlıklı federated learning veya çok-istemcili model birleştirme yoktur; öneri, replay
          değerlendirmesindeki precision/recall’dan üretilir. Gerçek görevlerde imzalı artefakt ve
          insan onayı gerekir. Zincir: <strong style={{ color: "#00F2FF" }}>orbiter sayacı</strong> →{" "}
          <strong style={{ color: "#FF00FF" }}>eşik önerisi</strong> → <strong style={{ color: "#00FF88" }}>RL geri besleme</strong>.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="n-hud p-5 rounded-lg border" style={{ borderColor: "#00F2FF30" }}>
          <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#607080" }}>
            GÜNCELLEME_TURU
          </p>
          <p className="text-4xl font-extrabold tabular-nums" style={{ color: "#00F2FF" }}>
            {lastRound}
          </p>
          <p className="text-[10px] mt-2 leading-snug" style={{ color: "#506070" }}>
            Yer bulutu tur sayacı · model_versions ile hizalı
          </p>
        </div>
        <div className="n-hud p-5 rounded-lg border" style={{ borderColor: "#FF00FF30" }}>
          <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#607080" }}>
            MODEL_SÜRÜMÜ
          </p>
          <p className="text-4xl font-extrabold tabular-nums" style={{ color: "#FF00FF" }}>
            {ecs?.model_version ?? merged[0]?.model_version ?? "—"}
          </p>
          <p className="text-[10px] mt-2" style={{ color: "#506070" }}>
            Sıralı sayaç (gerçek ağır model yok — mimari yer tutucu)
          </p>
        </div>
        <div className="n-hud p-5 rounded-lg border" style={{ borderColor: "#00FF8830" }}>
          <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#607080" }}>
            SON_EŞİK_ÖNERİSİ
          </p>
          <p className="text-4xl font-extrabold tabular-nums" style={{ color: "#00FF88" }}>
            {merged[0]?.threshold_suggestion != null ? merged[0].threshold_suggestion.toFixed(1) : "—"}
          </p>
          <p className="text-[10px] mt-2" style={{ color: "#506070" }}>
            Edge iletim eşiğine öneri (40–70 bandı)
          </p>
        </div>
        <div className="n-hud p-5 rounded-lg border" style={{ borderColor: "#FFAA0030" }}>
          <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: "#607080" }}>
            CLOUD_SENKRON
          </p>
          <p className="text-4xl font-extrabold tabular-nums" style={{ color: "#FFAA00" }}>
            {batchesLeft != null ? batchesLeft : "—"}
          </p>
          <p className="text-[10px] mt-2" style={{ color: "#506070" }}>
            Kalan orbiter batch (hedef: {everyN})
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="n-panel p-5 rounded-lg border" style={{ borderColor: "#0D1520" }}>
          <p className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "#607080" }}>
            Operasyonel hizmet düzeyi özeti
          </p>
          <ul className="space-y-2 text-xs font-mono" style={{ color: "#99AAB8" }}>
            <li className="flex justify-between border-b pb-2" style={{ borderColor: "#0D1520" }}>
              <span style={{ color: "#506070" }}>Orbiter tampon (canlı)</span>
              <span style={{ color: "#00F2FF" }}>{orb?.buffer_pending ?? "—"} paket</span>
            </li>
            <li className="flex justify-between border-b pb-2" style={{ borderColor: "#0D1520" }}>
              <span style={{ color: "#506070" }}>Pekiştirmeli öğrenme toplam ödülü</span>
              <span style={{ color: "#00FF88" }}>{stats?.rl_stats?.total_reward ?? "—"}</span>
            </li>
            <li className="flex justify-between border-b pb-2" style={{ borderColor: "#0D1520" }}>
              <span style={{ color: "#506070" }}>Pekiştirmeli ε (keşif)</span>
              <span style={{ color: "#FF00FF" }}>{stats?.rl_stats?.epsilon ?? "—"}</span>
            </li>
            <li className="flex justify-between">
              <span style={{ color: "#506070" }}>RL adım (Q-tablo)</span>
              <span>{stats?.rl_stats?.steps ?? "—"}</span>
            </li>
          </ul>
        </div>

        <div className="n-panel p-5 rounded-lg border" style={{ borderColor: "#0D1520" }}>
          <p className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "#607080" }}>
            Federated tur adımları
          </p>
          <ul className="space-y-3">
            {fedSteps.map((s) => (
              <li key={s.k} className="flex gap-3">
                <span
                  className="shrink-0 w-7 h-7 flex items-center justify-center rounded text-[10px] font-black"
                  style={{ background: "#FF00FF18", color: "#FF00FF", border: "1px solid #FF00FF44" }}
                >
                  {s.k}
                </span>
                <div>
                  <p className="text-xs font-bold uppercase" style={{ color: "#99AAB8" }}>
                    {s.t}
                  </p>
                  <p className="text-[11px] mt-0.5 leading-snug" style={{ color: "#607080" }}>
                    {s.d}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="n-panel p-4 rounded-lg border w-full" style={{ borderColor: "#0D1520", minHeight: 320 }}>
          <p className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "#607080" }}>
            Eşik önerisi · yer istasyonu turu
          </p>
          <div className="h-72 w-full">
            {timeline.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs" style={{ color: "#506070" }}>
                Eşik önerisi verisi yok — bulut senkronu sonrası dolar.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={timeline} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#0D1520" strokeDasharray="3 3" />
                  <XAxis dataKey="round" tick={{ fill: "#506070", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#506070", fontSize: 10 }} domain={[35, 75]} />
                  <Tooltip
                    contentStyle={{ background: "#080C14", border: "1px solid #0D1520", color: "#99AAB8" }}
                  />
                  <Bar dataKey="thr" fill="#FF00FF" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
        <div className="n-panel p-4 rounded-lg border w-full" style={{ borderColor: "#0D1520", minHeight: 320 }}>
          <p className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "#607080" }}>
            Pekiştirmeli öğrenme ödül geçmişi
          </p>
          <div className="h-72 w-full">
            {rewardChart.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs" style={{ color: "#506070" }}>
                Ödül serisi yok — toplam ödül her değiştiğinde nokta eklenir.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={rewardChart} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#0D1520" strokeDasharray="3 3" />
                  <XAxis dataKey="t" tick={{ fill: "#506070", fontSize: 9 }} />
                  <YAxis tick={{ fill: "#506070", fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ background: "#080C14", border: "1px solid #0D1520", color: "#99AAB8" }}
                  />
                  <Line type="monotone" dataKey="reward" stroke="#00FF88" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-lg border overflow-hidden" style={{ background: "#060910", borderColor: "#0D1520" }}>
        <div className="px-4 py-2.5 border-b flex justify-between" style={{ borderColor: "#0D1520" }}>
          <span className="text-xs font-bold uppercase" style={{ color: "#607080" }}>
            MODEL_GÜNCELLEME_GÜNLÜĞÜ
          </span>
          <span className="text-[10px] font-mono" style={{ color: "#506070" }}>
            GET /api/model-updates
          </span>
        </div>
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full text-xs font-mono">
            <thead style={{ color: "#506070" }}>
              <tr className="text-left border-b sticky top-0" style={{ borderColor: "#0D1520", background: "#060910" }}>
                <th className="p-2.5">Zaman</th>
                <th className="p-2.5">Tur</th>
                <th className="p-2.5">Model sürümü</th>
                <th className="p-2.5">Eşik önerisi</th>
                <th className="p-2.5">Kaynak</th>
              </tr>
            </thead>
            <tbody style={{ color: "#99AAB8" }}>
              {merged.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-6 text-center" style={{ color: "#506070" }}>
                    Henüz model güncellemesi yok — orbiter sayacı dolduğunda yer bulutu senkron döngüsü kayıt üretir.
                  </td>
                </tr>
              )}
              {merged.slice(0, 25).map((m) => (
                <tr key={m.id || `${m.federated_round}-${m.model_version}`} className="border-b" style={{ borderColor: "#0D1520" }}>
                  <td className="p-2.5 whitespace-nowrap">
                    {m.created_at ? new Date(m.created_at).toLocaleString("tr-TR") : m.at ? new Date(m.at).toLocaleString("tr-TR") : "—"}
                  </td>
                  <td className="p-2.5">{m.federated_round ?? "—"}</td>
                  <td className="p-2.5">{m.model_version ?? "—"}</td>
                  <td className="p-2.5" style={{ color: "#00FF88" }}>
                    {m.threshold_suggestion != null ? Number(m.threshold_suggestion).toFixed(2) : "—"}
                  </td>
                  <td className="p-2.5">{m.source ?? "earth_cloud"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
