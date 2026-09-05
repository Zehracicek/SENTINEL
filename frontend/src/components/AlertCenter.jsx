import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { hasApiToken, writeAuthHint } from "../utils/api";
import { formatNumber, formatTimestamp, severityColor } from "../utils/formatters";

const SEV_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

const SEV_LABEL_TR = {
  CRITICAL: "KRİTİK",
  HIGH: "YÜKSEK",
  MEDIUM: "ORTA",
  LOW: "DÜŞÜK",
};

function severityLabelTr(sev) {
  return SEV_LABEL_TR[sev] || sev;
}

const ANOM_TR = {
  organic_molecule: "ORGANİK_MOLEKÜL",
  methane_spike: "METAN_ARTIŞI",
  spectral_deviation: "SPEKTRAL_SAPMA",
  moisture_anomaly: "NEM_ANOMALİSİ",
  temperature_extreme: "SICAKLIK_EKSTREMİ",
  radiation_anomaly: "RADYASYON_ANOMALİSİ",
  atmospheric_anomaly: "ATMOSFER_ANOMALİSİ",
  pressure_anomaly: "BASINÇ_ANOMALİSİ",
};

const BAR_COLORS = ["#00F2FF", "#FF00FF", "#00FF88", "#FFAA00", "#FF3366", "#8899AA"];

function TypeDistributionTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const accent = d.barColor || "#00F2FF";
  const count = d.count;
  const avg = d.avg;
  return (
    <div
      style={{
        padding: "14px 16px",
        minWidth: "200px",
        background: "rgba(6, 9, 16, 0.94)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        border: `1px solid ${accent}55`,
        boxShadow: `0 0 32px ${accent}20, 0 12px 40px rgba(0,0,0,0.55)`,
        fontFamily: '"JetBrains Mono", ui-monospace, monospace',
      }}
    >
      <p
        className="text-[11px] font-bold uppercase tracking-widest mb-2.5"
        style={{
          color: accent,
          textShadow: `0 0 14px ${accent}45`,
        }}
      >
        {d.name}
      </p>
      <div className="space-y-1.5 text-[11px]">
        <div className="flex justify-between gap-8">
          <span style={{ color: "#506070" }} className="font-semibold uppercase tracking-wide">
            Sayı
          </span>
          <span style={{ color: "#BCC8D4" }}>
            <span className="font-bold tabular-nums">{formatNumber(count, 0)}</span>{" "}
            <span style={{ color: "#607080" }}>kayıt</span>
          </span>
        </div>
        <div className="flex justify-between gap-8">
          <span style={{ color: "#506070" }} className="font-semibold uppercase tracking-wide">
            Ort. öncelik
          </span>
          <span className="font-bold tabular-nums" style={{ color: "#FF00FF" }}>
            {avg != null && Number.isFinite(Number(avg)) ? Number(avg).toFixed(1) : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

function typeLabel(t) {
  return ANOM_TR[t] || t;
}

function shortUuid(id) {
  const s = String(id);
  if (s.length <= 10) return s;
  return `${s.slice(0, 8)}…`;
}

export default function AlertCenter({ anomalies, onAcknowledge, appendAnomaliesFromApi }) {
  const [filter, setFilter] = useState("ALL");
  const [ackFilter, setAckFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedTypes, setSelectedTypes] = useState(() => new Set());
  const [statsRows, setStatsRows] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [details, setDetails] = useState({});
  const [detailLoading, setDetailLoading] = useState(null);
  const [loadMoreLoading, setLoadMoreLoading] = useState(false);
  const [ackError, setAckError] = useState(null);
  const [ackingId, setAckingId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/anomalies/stats")
      .then((r) => (r.ok ? r.json() : []))
      .then((rows) => {
        if (!cancelled && Array.isArray(rows)) setStatsRows(rows);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const searchTrim = search.trim().toLowerCase();

  const uniqueTypes = useMemo(() => {
    const s = new Set();
    anomalies.forEach((a) => {
      if (a?.anomaly_type) s.add(a.anomaly_type);
    });
    return Array.from(s).sort();
  }, [anomalies]);

  const pipeline = useMemo(() => {
    let rows = anomalies;
    if (ackFilter === "pending") rows = rows.filter((a) => !a.acknowledged);
    else if (ackFilter === "ack") rows = rows.filter((a) => a.acknowledged);
    if (selectedTypes.size > 0) {
      rows = rows.filter((a) => selectedTypes.has(a.anomaly_type));
    }
    if (searchTrim) {
      rows = rows.filter((a) =>
        (a.description || "").toLowerCase().includes(searchTrim)
      );
    }
    return rows;
  }, [anomalies, ackFilter, selectedTypes, searchTrim]);

  const counts = useMemo(() => {
    const c = {
      ALL: pipeline.length,
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0,
    };
    pipeline.forEach((a) => {
      const k = a.severity;
      if (k && c[k] !== undefined) c[k] += 1;
    });
    return c;
  }, [pipeline]);

  const filtered = useMemo(() => {
    const base =
      filter === "ALL"
        ? [...pipeline]
        : pipeline.filter((a) => a.severity === filter);
    return base.sort(
      (a, b) =>
        (SEV_ORDER[a.severity] ?? 9) - (SEV_ORDER[b.severity] ?? 9)
    );
  }, [pipeline, filter]);

  const chartData = useMemo(
    () =>
      [...statsRows]
        .sort((a, b) => b.count - a.count)
        .map((r, i) => ({
          name: typeLabel(r.anomaly_type),
          count: r.count,
          avg: r.avg_priority,
          key: r.anomaly_type,
          barColor: BAR_COLORS[i % BAR_COLORS.length],
        })),
    [statsRows]
  );

  const toggleType = useCallback((t) => {
    setSelectedTypes((prev) => {
      const n = new Set(prev);
      if (n.has(t)) n.delete(t);
      else n.add(t);
      return n;
    });
  }, []);

  const clearTypes = useCallback(() => setSelectedTypes(new Set()), []);

  const handleAcknowledge = useCallback(
    async (id) => {
      if (!onAcknowledge) return;
      setAckingId(String(id));
      setAckError(null);
      const result = await onAcknowledge(id);
      if (result && !result.ok) {
        setAckError(result.error || writeAuthHint() || "Onaylanamadı");
      }
      setAckingId(null);
    },
    [onAcknowledge]
  );

  const copyId = useCallback((id) => {
    navigator.clipboard?.writeText(String(id)).catch(() => {});
  }, []);

  const toggleExpand = useCallback(
    async (id) => {
      const sid = String(id);
      if (expandedId === sid) {
        setExpandedId(null);
        return;
      }
      setExpandedId(sid);
      if (details[sid]) return;
      setDetailLoading(sid);
      try {
        const r = await fetch(`/api/anomalies/${id}/detail`);
        if (r.ok) {
          const d = await r.json();
          setDetails((prev) => ({ ...prev, [sid]: d }));
        }
      } catch {
        /* ignore */
      } finally {
        setDetailLoading(null);
      }
    },
    [expandedId, details]
  );

  const handleLoadMore = useCallback(async () => {
    if (!appendAnomaliesFromApi || loadMoreLoading) return;
    setLoadMoreLoading(true);
    try {
      const r = await fetch(
        `/api/anomalies?skip=${anomalies.length}&limit=100`
      );
      const rows = r.ok ? await r.json() : [];
      appendAnomaliesFromApi(rows);
    } catch {
      /* ignore */
    } finally {
      setLoadMoreLoading(false);
    }
  }, [anomalies.length, appendAnomaliesFromApi, loadMoreLoading]);

  const items = [
    { k: "CRITICAL", c: "#FF3366", l: "KRİTİK" },
    { k: "HIGH", c: "#FF8800", l: "YÜKSEK" },
    { k: "MEDIUM", c: "#FFAA00", l: "ORTA" },
    { k: "LOW", c: "#00F2FF", l: "DÜŞÜK" },
  ];

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {items.map((s) => (
          <div
            key={s.k}
            className="n-hud p-5"
            style={{
              background: "linear-gradient(135deg, #080C14, #060910)",
            }}
          >
            <p className="n-label">{s.l}</p>
            <p
              className="text-3xl font-extrabold mt-2"
              style={{
                color: s.c,
                textShadow: `0 0 12px ${s.c}35`,
              }}
            >
              {counts[s.k] || 0}
            </p>
            <div
              className="mt-3 h-px"
              style={{
                background: `linear-gradient(to right, ${s.c}30, transparent 70%)`,
              }}
            />
          </div>
        ))}
      </div>

      <div className="n-hud p-6" style={{ background: "#080C14" }}>
        <p className="n-label mb-4">ANOMALİ_TİP_DAĞILIMI</p>
        {chartData.length === 0 ? (
          <div
            className="h-40 flex items-center justify-center text-xs uppercase tracking-wider"
            style={{ color: "#2A3A4D" }}
          >
            İSTATİSTİK_BEKLENİYOR
          </div>
        ) : (
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
              >
                <XAxis type="number" tick={{ fill: "#506070", fontSize: 10 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={120}
                  tick={{ fill: "#708090", fontSize: 9 }}
                />
                <Tooltip
                  content={<TypeDistributionTooltip />}
                  cursor={{ fill: "rgba(0, 242, 255, 0.07)" }}
                  wrapperStyle={{ outline: "none", zIndex: 50 }}
                  allowEscapeViewBox={{ x: true, y: true }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} isAnimationActive={false}>
                  {chartData.map((_, i) => (
                    <Cell
                      key={chartData[i].key}
                      fill={BAR_COLORS[i % BAR_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="n-hud p-6" style={{ background: "#080C14" }}>
        <div className="flex flex-col gap-4 mb-5">
          <p className="n-label">ALARM_MERKEZİ</p>

          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs uppercase tracking-wider" style={{ color: "#506070" }}>
              Onay:
            </span>
            {[
              { k: "all", l: "Tümü" },
              { k: "pending", l: "Bekleyen" },
              { k: "ack", l: "Onaylanmış" },
            ].map((x) => {
              const on = ackFilter === x.k;
              return (
                <button
                  key={x.k}
                  type="button"
                  onClick={() => setAckFilter(x.k)}
                  className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-all"
                  style={{
                    background: on
                      ? "linear-gradient(135deg, #FF00FF12, #FF00FF06)"
                      : "transparent",
                    border: `1px solid ${on ? "#FF00FF40" : "#0D1520"}`,
                    color: on ? "#FF00FF" : "#2A3A4D",
                  }}
                >
                  {x.l}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs uppercase tracking-wider" style={{ color: "#506070" }}>
              Tip:
            </span>
            <button
              type="button"
              onClick={clearTypes}
              className="px-2 py-1 text-xs font-bold uppercase"
              style={{ color: "#00F2FF", border: "1px solid #00F2FF30" }}
            >
              Tüm tipler
            </button>
            {uniqueTypes.map((t) => {
              const on = selectedTypes.has(t);
              return (
                <button
                  key={t}
                  type="button"
                  onClick={() => toggleType(t)}
                  className="px-2 py-1 text-xs font-bold uppercase max-w-[140px] truncate"
                  style={{
                    background: on ? "#00F2FF14" : "transparent",
                    border: `1px solid ${on ? "#00F2FF50" : "#0D1520"}`,
                    color: on ? "#00F2FF" : "#506070",
                  }}
                  title={t}
                >
                  {typeLabel(t)}
                </button>
              );
            })}
          </div>

          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Açıklamada ara…"
            className="w-full max-w-md px-3 py-2 text-sm rounded-none font-mono"
            style={{
              background: "#04060A",
              border: "1px solid #0D1520",
              color: "#8899AA",
            }}
          />
          {(ackError || !hasApiToken()) && (
            <p className="text-xs font-mono leading-relaxed mt-3" style={{ color: "#FF3366" }}>
              {ackError || writeAuthHint()}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div className="flex gap-1.5 flex-wrap">
            {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => {
              const on = filter === s;
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => setFilter(s)}
                  className="px-3 py-1.5 text-xs font-bold uppercase tracking-wide transition-all"
                  style={{
                    background: on
                      ? "linear-gradient(135deg, #00F2FF12, #00F2FF06)"
                      : "transparent",
                    border: `1px solid ${on ? "#00F2FF40" : "#0D1520"}`,
                    color: on ? "#00F2FF" : "#2A3A4D",
                    textShadow: on ? "0 0 8px #00F2FF30" : "none",
                  }}
                >
                  {s === "ALL"
                    ? `ŞİDDET: TÜMÜ (${counts.ALL})`
                    : `${severityLabelTr(s)} (${counts[s] || 0})`}
                </button>
              );
            })}
          </div>
          {appendAnomaliesFromApi && (
            <button
              type="button"
              onClick={handleLoadMore}
              disabled={loadMoreLoading}
              className="px-4 py-2 text-xs font-bold uppercase"
              style={{
                border: "1px solid #00F2FF40",
                color: "#00F2FF",
                opacity: loadMoreLoading ? 0.5 : 1,
              }}
            >
              {loadMoreLoading ? "YÜKLENİYOR…" : "Daha fazla yükle"}
            </button>
          )}
        </div>

        {filtered.length === 0 ? (
          <div
            className="text-center text-sm py-16 uppercase tracking-wider"
            style={{ color: "#2A3A4D" }}
          >
            FİLTRE_İLE_EŞLEŞEN_ALARM_YOK
          </div>
        ) : (
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {filtered.map((a) => {
              const ss = severityColor(a.severity);
              const isCrit = a.severity === "CRITICAL" && !a.acknowledged;
              const sid = String(a.id);
              const open = expandedId === sid;
              const detail = details[sid];
              const loadingD = detailLoading === sid;
              return (
                <div
                  key={sid}
                  className={`p-4 transition-all ${isCrit ? "animate-critical" : ""}`}
                  style={{
                    background: a.acknowledged
                      ? "#04060A"
                      : isCrit
                        ? "#FF33660A"
                        : "#050810",
                    border: `1px solid ${
                      a.acknowledged
                        ? "#0A0F18"
                        : isCrit
                          ? "#FF336630"
                          : "#0D1520"
                    }`,
                    opacity: a.acknowledged ? 0.72 : 1,
                    boxShadow: isCrit ? "0 0 16px #FF33660A" : "none",
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <span
                          className="px-3 py-1 text-xs font-bold uppercase"
                          style={{
                            background: ss.bg,
                            color: ss.text,
                            border: `1px solid ${ss.border}`,
                            textShadow: `0 0 6px ${ss.text}30`,
                            boxShadow: `0 0 8px ${ss.text}08`,
                          }}
                        >
                          {severityLabelTr(a.severity)}
                        </span>
                        <span
                          className="text-sm font-bold uppercase tracking-wide"
                          style={{
                            color: "#00F2FF",
                            textShadow: "0 0 8px #00F2FF20",
                          }}
                        >
                          {typeLabel(a.anomaly_type)}
                        </span>
                        <span
                          className="text-xs font-mono"
                          style={{ color: "#506070" }}
                        >
                          Öncelik{" "}
                          <span
                            className="font-bold"
                            style={{ color: "#FF00FF" }}
                          >
                            {a.scientific_priority}/10
                          </span>
                        </span>
                        <span
                          className="text-xs ml-auto"
                          style={{ color: "#2A3A4D" }}
                        >
                          {formatTimestamp(a.created_at)}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <span className="text-xs font-mono" style={{ color: "#3A4A5C" }}>
                          okuma_kimliği: {shortUuid(a.reading_id)}
                        </span>
                        <button
                          type="button"
                          onClick={() => copyId(a.reading_id)}
                          className="text-xs uppercase font-bold"
                          style={{ color: "#00F2FF" }}
                        >
                          Kopyala
                        </button>
                      </div>
                      <p
                        className={`text-sm leading-relaxed ${open ? "" : "line-clamp-2"}`}
                        style={{ color: "#4A5568" }}
                      >
                        {a.description}
                      </p>
                      <button
                        type="button"
                        onClick={() => toggleExpand(a.id)}
                        className="text-xs font-bold uppercase mt-2 tracking-wide"
                        style={{ color: "#607080" }}
                      >
                        {open ? "Detayı gizle" : "Detay + ölçüm"}
                      </button>
                      {open && (
                        <div
                          className="mt-3 p-3 text-xs space-y-2 font-mono"
                          style={{
                            background: "#04060A",
                            border: "1px solid #0D1520",
                          }}
                        >
                          {loadingD && (
                            <p style={{ color: "#506070" }}>Yükleniyor…</p>
                          )}
                          {!loadingD && detail?.reading && (
                            <>
                              <p style={{ color: "#708090" }}>
                                <span style={{ color: "#00F2FF" }}>
                                  {detail.reading.sensor_type}
                                </span>{" "}
                                ham={detail.reading.raw_value}{" "}
                                {detail.reading.unit} · skor{" "}
                                {detail.reading.anomaly_score} · SOL{" "}
                                {detail.reading.sol} · iletim:{" "}
                                {detail.reading.is_transmitted ? "evet" : "hayır"}
                              </p>
                            </>
                          )}
                          {!loadingD && detail && !detail.reading && (
                            <p style={{ color: "#506070" }}>
                              Okuma kaydı bulunamadı.
                            </p>
                          )}
                          {!loadingD && !detail && (
                            <p style={{ color: "#506070" }}>
                              Detay alınamadı.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                    {!a.acknowledged ? (
                      <button
                        type="button"
                        disabled={ackingId === String(a.id)}
                        onClick={() => handleAcknowledge(a.id)}
                        className="n-btn-primary text-xs py-2 px-4 shrink-0"
                      >
                        {ackingId === String(a.id) ? "…" : "ONAYLA"}
                      </button>
                    ) : (
                      <span
                        className="text-xs font-bold uppercase tracking-wider shrink-0 text-glow-green"
                        style={{ color: "#00FF88" }}
                      >
                        ONAYLANDI
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
