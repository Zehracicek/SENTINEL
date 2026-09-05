import { useEffect, useState } from "react";
import { formatNumber } from "../utils/formatters";

export default function UplinkQueue({ statsQueue }) {
  const [snap, setSnap] = useState(null);

  useEffect(() => {
    fetch("/api/uplink-queue")
      .then((r) => (r.ok ? r.json() : null))
      .then(setSnap)
      .catch(() => setSnap(null));
  }, []);

  useEffect(() => {
    if (statsQueue) setSnap(statsQueue);
  }, [statsQueue]);

  if (!snap) {
    return (
      <div className="n-hud p-10 text-center text-sm animate-pulse" style={{ color: "#506070" }}>
        UPLINK_KUYRUĞU_YÜKLENİYOR...
      </div>
    );
  }

  const { pending_total = 0, sent_total = 0, pending = [], recent_sent = [] } = snap;

  return (
    <div className="space-y-5">
      <div>
        <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>
          UPLINK_KUYRUĞU
        </p>
        <p className="text-sm mt-1 max-w-3xl leading-relaxed" style={{ color: "#708090" }}>
          Skor ≥ 50 olan paketler önce veritabanında <strong style={{ color: "#00F2FF" }}>bekleyen</strong> kuyruğa alınır;
          simülasyon her <strong style={{ color: "#FF00FF" }}>10 saniyede</strong> bir önceliğe göre en fazla <strong style={{ color: "#FF00FF" }}>6</strong> paketi DSN üzerinden
          iletir (<strong style={{ color: "#00FF88" }}>iletildi</strong> durumu). Bu, bant kısıtını ve sıralı uplink davranışını yansıtır.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { l: "KUYRUKTAKİ", v: pending_total.toLocaleString("tr-TR"), c: "#FFAA00" },
          { l: "İLETİLMİŞ (toplam)", v: sent_total.toLocaleString("tr-TR"), c: "#00FF88" },
          { l: "LİSTE (bekleyen)", v: pending.length.toString(), c: "#00F2FF" },
          { l: "SON İLETİLEN (liste)", v: recent_sent.length.toString(), c: "#FF00FF" },
        ].map((x) => (
          <div key={x.l} className="n-hud p-4" style={{ background: "linear-gradient(135deg, #080C14, #060910)" }}>
            <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#506070" }}>{x.l}</p>
            <p className="text-2xl font-extrabold mt-1" style={{ color: x.c, textShadow: `0 0 10px ${x.c}35` }}>{x.v}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#FFAA00" }}>
            SIRADA_BEKLEYEN (öncelik ↓)
          </p>
          <div className="space-y-2 max-h-[420px] overflow-y-auto">
            {pending.length === 0 ? (
              <p className="text-sm py-8 text-center" style={{ color: "#506070" }}>KUYRUK_BOŞ</p>
            ) : (
              pending.map((p, i) => (
                <div
                  key={p.queue_id}
                  className="flex items-center justify-between gap-3 px-3 py-2.5 text-xs font-mono"
                  style={{ background: "#050810", border: "1px solid #1A2535" }}
                >
                  <span style={{ color: "#506070" }}>#{i + 1}</span>
                  <span className="font-bold" style={{ color: "#00F2FF" }}>{p.sensor_type}</span>
                  <span style={{ color: "#8899AA" }}>öncelik {formatNumber(p.uplink_priority, 1)}</span>
                  <span className="truncate max-w-[100px]" style={{ color: "#607080" }} title={p.queued_at}>
                    {p.queued_at?.slice(11, 19) || "—"}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#00FF88" }}>
            SON_İLETİLENLER
          </p>
          <div className="space-y-2 max-h-[420px] overflow-y-auto">
            {recent_sent.length === 0 ? (
              <p className="text-sm py-8 text-center" style={{ color: "#506070" }}>HENÜZ_İLETİM_YOK</p>
            ) : (
              recent_sent.map((p) => (
                <div
                  key={p.queue_id}
                  className="flex flex-col gap-1 px-3 py-2.5 text-xs font-mono"
                  style={{ background: "#050810", border: "1px solid #0D1520" }}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold" style={{ color: "#FF00FF" }}>{p.sensor_type}</span>
                    <span style={{ color: "#607080" }}>{p.sent_at?.slice(11, 19) || "—"}</span>
                  </div>
                  <div className="flex justify-between" style={{ color: "#708090" }}>
                    <span>DSN: <span style={{ color: "#00F2FF" }}>{p.dsn_station || "—"}</span></span>
                    <span>skor {formatNumber(p.anomaly_score, 1)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
