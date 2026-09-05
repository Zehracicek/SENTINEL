import { useEffect, useState } from "react";
import { formatNumber } from "../utils/formatters";

const POLL_MS = 15000;

function pct(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `%${formatNumber(Number(n) * 100, 1)}`;
}

function Metric({ label, value, color, sub }) {
  return (
    <div className="text-center p-4" style={{ background: "#050810", border: "1px solid #0D1520" }}>
      <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>{label}</p>
      <p className="text-3xl font-extrabold mt-2" style={{ color, textShadow: `0 0 14px ${color}40` }}>{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: "#506070" }}>{sub}</p>}
    </div>
  );
}

export default function EvaluationMetrics({ compact = false }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      fetch("/api/evaluation/detection")
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
        .then((j) => {
          if (!cancelled) {
            setData(j);
            setError(null);
          }
        })
        .catch((e) => {
          if (!cancelled) setError(e.message || "alınamadı");
        });
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const source = data?.anomaly_score_source || "—";
  const lstm = String(source).includes("lstm");

  if (error && !data) {
    return (
      <div className="n-hud p-5">
        <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#FF3366" }}>
          DEĞERLENDİRME_ALINAMADI
        </p>
        <p className="text-sm mt-2" style={{ color: "#708090" }}>
          /api/evaluation/detection yanıt vermiyor ({error}). Backend ayakta mı?
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="n-hud p-5">
        <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>
          DEĞERLENDİRME_YÜKLENİYOR
        </p>
      </div>
    );
  }

  const n = data.evaluated_readings || 0;

  return (
    <div className="n-hud p-5 space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>
            BU_SİSTEMİN_ÖLÇÜMÜ
          </p>
          <p className="text-sm mt-1" style={{ color: "#8899AA" }}>
            `is_anomaly` (uç kararı) × `ground_truth_anomaly` (veri seti etiketi). Makale skoru değil.
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>
            SKOR_KAYNAĞI
          </p>
          <p className="text-sm font-bold mt-1" style={{ color: lstm ? "#00FF88" : "#FFAA00" }}>
            {source}
          </p>
        </div>
      </div>

      <div className={`grid grid-cols-2 ${compact ? "lg:grid-cols-4" : "lg:grid-cols-4"} gap-3`}>
        <Metric label="NOKTA_PRECISION" value={pct(data.precision)} color="#00FF88" sub={`${data.true_positives} TP / ${data.true_positives + data.false_positives} işaret`} />
        <Metric label="NOKTA_RECALL" value={pct(data.recall)} color="#00F2FF" sub={`${data.true_positives} TP / ${data.true_positives + data.false_negatives} gerçek`} />
        <Metric label="NOKTA_F1" value={formatNumber(data.f1_score, 3)} color="#FF00FF" sub={`F0.5 ${formatNumber(data.f_half_score, 3)}`} />
        <Metric
          label="İŞARET_ORANI"
          value={pct(data.predicted_anomaly_rate)}
          color={data.predicted_anomaly_rate > 0.4 ? "#FF3366" : "#FFAA00"}
          sub={`etiket ${pct(data.ground_truth_anomaly_rate)} · ${n.toLocaleString("tr-TR")} okuma`}
        />
      </div>

      {data.sequence_evaluated ? (
        <div className={`grid grid-cols-2 ${compact ? "lg:grid-cols-4" : "lg:grid-cols-4"} gap-3`}>
          <Metric
            label="DİZİ_PRECISION"
            value={pct(data.sequence_precision)}
            color="#66FFCC"
            sub={`${data.sequence_pred_true_positives} örtüşen / ${data.sequence_predicted_count} tahmin dizisi`}
          />
          <Metric
            label="DİZİ_RECALL"
            value={pct(data.sequence_recall)}
            color="#66DDFF"
            sub={`${data.sequence_true_positives} yakalanan / ${data.sequence_true_count} gerçek dizi`}
          />
          <Metric
            label="DİZİ_F1"
            value={formatNumber(data.sequence_f1_score, 3)}
            color="#EE88FF"
            sub={`F0.5 ${formatNumber(data.sequence_f_half_score, 3)} · Hundman örtüşme`}
          />
          <Metric
            label="DİZİ_HATA"
            value={`${data.sequence_false_positives} FP`}
            color="#FFAA00"
            sub={`${data.sequence_false_negatives} FN · ${data.sequence_indexed_readings?.toLocaleString("tr-TR")} indeksli`}
          />
        </div>
      ) : (
        <p className="text-xs" style={{ color: "#506070" }}>
          Dizi metrikleri henüz yok — `replay_index` için migration 008 ve yeni replay okumaları gerekir.
        </p>
      )}

      {!compact && (
        <>
          <div className="grid grid-cols-4 gap-3">
            {[
              { l: "TP", v: data.true_positives, c: "#00FF88" },
              { l: "FP", v: data.false_positives, c: "#FFAA00" },
              { l: "FN", v: data.false_negatives, c: "#FF3366" },
              { l: "TN", v: data.true_negatives, c: "#8899AA" },
            ].map((m) => (
              <div key={m.l} className="text-center p-3" style={{ background: "#050810", border: "1px solid #0D1520" }}>
                <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>{m.l}</p>
                <p className="text-xl font-extrabold mt-1" style={{ color: m.c }}>{Number(m.v || 0).toLocaleString("tr-TR")}</p>
              </div>
            ))}
          </div>
          <p className="text-xs leading-relaxed" style={{ color: "#607080" }}>
            {data.note}
            {" "}
            LSTM `smoothed_errors` yokken F1 ≈ 0.25 beklenir; eşik ayarı yalnızca precision/recall takası yapar.
          </p>
        </>
      )}
    </div>
  );
}
