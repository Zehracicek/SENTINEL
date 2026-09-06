import { useEffect, useState } from "react";
import { apiFetch, hasApiToken, writeAuthHint } from "../utils/api";
import { formatTimestamp } from "../utils/formatters";

const TYPE_MS = 80;

function DecisionBox({ decision, uplinkEligible }) {
  const s = String(decision || "");
  const hasDrop = /\bDROP\b/i.test(s) || /\bATLA\b/i.test(s);
  const hasTx = /\bTX\b/i.test(s) || /İLET|ILET/i.test(s);
  const showTx =
    hasDrop && hasTx ? false : hasDrop ? false : hasTx ? true : uplinkEligible !== false;
  return (
    <div
      className="mt-4 px-4 py-3 rounded border text-center font-bold uppercase tracking-widest text-sm"
      style={{
        borderColor: showTx ? "#00FF8844" : "#FF336688",
        background: showTx ? "linear-gradient(180deg, #00FF8812, transparent)" : "linear-gradient(180deg, #FF336612, transparent)",
        color: showTx ? "#00FF88" : "#FF3366",
        boxShadow: showTx ? "0 0 24px #00FF8830" : "0 0 24px #FF336630",
      }}
    >
      {showTx ? "✅ İLETİLİYOR" : "❌ ATLANDI"}
    </div>
  );
}

export default function RoverThinking({ entries = [], stats = null }) {
  const [visibleSteps, setVisibleSteps] = useState([]);
  const [modal, setModal] = useState(null);
  const [thinkOn, setThinkOn] = useState(stats?.rover_thinking_enabled === true);
  const [saving, setSaving] = useState(false);
  const [toggleError, setToggleError] = useState(null);
  const latest = entries[0];

  useEffect(() => {
    if (typeof stats?.rover_thinking_enabled === "boolean") {
      setThinkOn(stats.rover_thinking_enabled);
    }
  }, [stats?.rover_thinking_enabled]);

  const toggleThinking = async () => {
    const next = !thinkOn;
    setSaving(true);
    setToggleError(null);
    try {
      const j = await apiFetch("/api/settings/rover-thinking", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: next }),
      });
      setThinkOn(!!j.enabled);
    } catch (err) {
      setToggleError(err.message || writeAuthHint() || "Ayar güncellenemedi");
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    const steps = Array.isArray(latest?.steps) ? latest.steps.filter((s) => String(s).trim()) : [];
    setVisibleSteps([]);
    if (steps.length === 0) return undefined;
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setVisibleSteps(steps.slice(0, i));
      if (i >= steps.length) clearInterval(id);
    }, TYPE_MS);
    return () => clearInterval(id);
  }, [latest?.timestamp, latest?.thinking]);

  const simInt = stats?.simulation_interval_seconds;

  return (
    <div className="w-full space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1
          className={`text-xl font-black uppercase tracking-[0.2em] ${thinkOn ? "animate-pulse" : ""}`}
          style={{
            color: thinkOn ? "#00FF88" : "#506070",
            textShadow: thinkOn ? "0 0 20px #00FF8860" : "none",
          }}
        >
          SENTİNEL Düşünce Modu
        </h1>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            disabled={saving}
            onClick={toggleThinking}
            className="px-4 py-2 rounded border text-xs font-bold uppercase tracking-widest transition-all"
            style={{
              borderColor: thinkOn ? "#00FF8866" : "#FF336666",
              background: thinkOn ? "linear-gradient(180deg, #00FF8818, transparent)" : "#1A1014",
              color: thinkOn ? "#00FF88" : "#FF3366",
              boxShadow: thinkOn ? "0 0 20px #00FF8830" : "none",
            }}
          >
            {saving ? "…" : thinkOn ? "⏸ Durdur" : "▶ Başlat"}
          </button>
          <span className="text-[11px] font-mono uppercase" style={{ color: "#607080" }}>
            {thinkOn ? "Groq çağrıları açık" : "Groq çağrıları kapalı"}
          </span>
        </div>
      </div>
      {(toggleError || !hasApiToken()) && (
        <p className="text-xs font-mono leading-relaxed" style={{ color: "#FF3366" }}>
          {toggleError || writeAuthHint()}
        </p>
      )}
      {stats && stats.groq_configured === false && (
        <p className="text-xs font-mono leading-relaxed" style={{ color: "#FFAA00" }}>
          Groq anahtarı yok; düşünce kartları üretilmez. backend/.env içindeki GROQ_API_KEY
          bir kez yazılır, sonraki açılışlarda kalır.
        </p>
      )}

      <div
        className="rounded-lg border px-4 py-3 text-xs font-mono leading-relaxed"
        style={{ background: "#080C14", borderColor: "#0D1520", color: "#708090" }}
      >
        <p>
          <span style={{ color: "#00F2FF" }}>Gecikme:</span> Her yüksek skorlu okuma için sunucu, Groq isteğinden önce yaklaşık{" "}
          <strong style={{ color: "#99AAB8" }}>10 sn</strong> bekler (ortam:{" "}
          <code className="text-[10px]" style={{ color: "#506070" }}>ROVER_THINK_DELAY_SECONDS</code>). Simülasyon turu aralığı:{" "}
          <strong style={{ color: "#99AAB8" }}>{simInt != null ? `${simInt} sn` : "—"}</strong>{" "}
          (<code className="text-[10px]" style={{ color: "#506070" }}>SENTINEL_SIM_INTERVAL_SECONDS</code>;{" "}
          <span style={{ color: "#506070" }}>eski:</span>{" "}
          <code className="text-[10px]" style={{ color: "#506070" }}>NIRVANA_SIM_INTERVAL_SECONDS</code>).
        </p>
      </div>

      {!latest && (
        <p className="text-sm font-mono" style={{ color: "#506070" }}>
          Anomali skoru ≥ 50 okumalarında Groq düşünce akışı burada görünür. Mod kapalıysa yeni çağrı yapılmaz. Bekleniyor…
        </p>
      )}

      {latest && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div
            className="rounded-lg p-4 border space-y-2"
            style={{ background: "#080C14", borderColor: "#00F2FF33", boxShadow: "0 0 40px #00F2FF10" }}
          >
            <p className="text-xs font-bold uppercase tracking-wider" style={{ color: "#00F2FF" }}>
              Sensör özeti
            </p>
            <ul className="text-sm font-mono space-y-1" style={{ color: "#99AAB8" }}>
              <li>
                <span style={{ color: "#506070" }}>Kanal:</span> {latest.channel_id}
              </li>
              <li>
                <span style={{ color: "#506070" }}>Skor:</span>{" "}
                <span style={{ color: "#FF00FF" }}>{Number(latest.anomaly_score).toFixed(1)}</span>
              </li>
              <li>
                <span style={{ color: "#506070" }}>Yenilik:</span>{" "}
                {latest.is_novel ? "EVET" : "HAYIR"}{" "}
                {latest.novelty_similarity != null && (
                  <span style={{ color: "#506070" }}>(benzerlik {Number(latest.novelty_similarity).toFixed(2)})</span>
                )}
              </li>
              <li>
                <span style={{ color: "#506070" }}>Enerji:</span>{" "}
                {latest.energy_level != null ? `%${Number(latest.energy_level).toFixed(0)}` : "—"}
              </li>
              <li>
                <span style={{ color: "#506070" }}>Zaman:</span> {formatTimestamp(latest.timestamp)}
              </li>
            </ul>
            <DecisionBox decision={latest.decision} uplinkEligible={latest.uplink_eligible} />
            <p className="text-center text-xs font-mono mt-2" style={{ color: "#607080" }}>
              ⚡ {latest.duration_ms ?? 0}ms — {latest.model ?? "—"}
            </p>
          </div>

          <div
            className="rounded-lg p-4 border min-h-[200px]"
            style={{ background: "#050810", borderColor: "#00FF8833" }}
          >
            <p className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: "#00FF88" }}>
              Adımlar
            </p>
            <div className="font-mono text-sm leading-relaxed space-y-1" style={{ color: "#00FF88", textShadow: "0 0 8px #00FF8830" }}>
              {visibleSteps.length === 0 && <span style={{ color: "#3A4A5C" }}>…</span>}
              {visibleSteps.map((line, idx) => (
                <div key={`${latest.timestamp}-${idx}`} className="border-l-2 pl-2" style={{ borderColor: "#00FF8844" }}>
                  {line}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div>
        <p className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: "#708090" }}>
          Son {Math.min(5, entries.length)} düşünce
        </p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {entries.map((e, i) => (
            <button
              key={`${e.timestamp}-${i}`}
              type="button"
              onClick={() => setModal(e)}
              className="text-left rounded-lg p-3 border transition-all hover:brightness-110"
              style={{
                background: "#080C14",
                borderColor: "#0D1520",
                boxShadow: i === 0 ? "0 0 16px #00F2FF15" : "none",
              }}
            >
              <div className="flex justify-between items-start gap-2">
                <span className="font-mono text-sm font-bold" style={{ color: "#00F2FF" }}>
                  {e.channel_id}
                </span>
                <span className="text-xs font-mono" style={{ color: "#FF00FF" }}>
                  {Number(e.anomaly_score).toFixed(0)}
                </span>
              </div>
              <p className="text-xs mt-1 line-clamp-2 font-mono" style={{ color: "#607080" }}>
                {(e.thinking || "").slice(0, 120)}
                {(e.thinking || "").length > 120 ? "…" : ""}
              </p>
              <p className="text-[10px] mt-2 font-mono uppercase" style={{ color: "#506070" }}>
                {e.decision} · {formatTimestamp(e.timestamp)}
              </p>
            </button>
          ))}
        </div>
      </div>

      {modal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "#000000cc" }}
          onClick={() => setModal(null)}
          onKeyDown={(ev) => ev.key === "Escape" && setModal(null)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="max-w-2xl w-full max-h-[85vh] overflow-y-auto rounded-xl border p-5"
            style={{ background: "#060910", borderColor: "#00F2FF44", boxShadow: "0 0 60px #00F2FF20" }}
            onClick={(ev) => ev.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold uppercase tracking-wide" style={{ color: "#00F2FF" }}>
                {modal.channel_id}
              </h2>
              <button
                type="button"
                className="text-xs uppercase font-bold px-2 py-1 rounded"
                style={{ color: "#FF3366", border: "1px solid #FF336644" }}
                onClick={() => setModal(null)}
              >
                Kapat
              </button>
            </div>
            <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed" style={{ color: "#99AAB8" }}>
              {modal.thinking || "(boş)"}
            </pre>
            <DecisionBox decision={modal.decision} uplinkEligible={modal.uplink_eligible} />
            <p className="text-center text-xs font-mono mt-3" style={{ color: "#506070" }}>
              ⚡ {modal.duration_ms ?? 0}ms — {modal.model ?? "—"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
