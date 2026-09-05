import { useState, useEffect, useRef } from "react";

const STEPS = [
  { id: "collect", num: "01", title: "VERİ TOPLAMA", sub: "SENSÖR OKUMA",
    color: "#00F2FF", icon: "📡",
    desc: "MSL (Curiosity) telemetrisine dayalı NASA SMAP/MSL veri setinden 12 kanal okunur (T-1, M-6, C-1, …). Gerçek görevde REMS, SAM, ChemCam vb. enstrümanlar benzer ölçüm türlerini üretir; bu paneldeki akış veri seti replay + edge simülasyonudur.",
    detail: "Kullanılan kanallar: T-1 (Sıcaklık), M-6 (Metan), C-1/C-2 (Spektrometre), D-14 (UV), D-15 (O₂), D-16 (CO₂), P-10 (Basınç), F-7 (FTIR). Veriler normalize edilmiş [-1, 1] aralığında, CCSDS paket formatında üretilir.",
    metrics: [
      { l: "KANAL SAYISI", v: "12 MSL kanalı" },
      { l: "OKUMA HIZI", v: "Varsayılan 10 sn / 12 paket" },
      { l: "VERİ FORMATI", v: "NumPy (.npy) → JSON" },
    ]},
  { id: "buffer", num: "02", title: "TAMPONLAMA", sub: "UÇ TAMPONU (SSR)",
    color: "#7000FF", icon: "💾",
    desc: "Toplanan ham veriler rover'ın Solid State Recorder (SSR) birimine yazılır. Ring buffer (dairesel tampon) yapısıyla en güncel veriler tutulur. Eski veriler otomatik olarak üzerine yazılır.",
    detail: "Her sensör tipi için ayrı buffer — 500 okuma kapasiteli dairesel yapı. Kritik veriler (yüksek anomali skoru) anında bir sonraki adıma geçer, düşük öncelikli veriler sırada bekler.",
    metrics: [
      { l: "TAMPON_KAPASİTESİ", v: "500 okuma / sensör" },
      { l: "YAPI", v: "Dairesel ring tampon" },
      { l: "DEPOLAMA", v: "SSR — katı hal kaydedici" },
    ]},
  { id: "anomaly", num: "03", title: "ANOMALİ TESPİTİ", sub: "Z-SCORE + RIVER (LSTM OPSİYONEL)",
    color: "#FFAA00", icon: "🔬",
    desc: "Skor iki sinyalin ağırlıklı ortalamasıdır. smoothed_errors/*.npy varsa LSTM hata sinyali (%50) + River (%50); yoksa z-score (%40) + kalibre River (%60). Keras çalışma anında yüklenmez.",
    detail: "River HalfSpaceTrees ham skoru yüzdelik sıraya çevrilir (sabit 70–97 tabanı yok). Canlı precision/recall VERİ_SETİ sayfasındadır. Makalenin %87.5 / %80 sonucu bu boru hattına ait değildir.",
    metrics: [
      { l: "LSTM", v: "Yalnızca smoothed_errors varsa" },
      { l: "YEDEK", v: "z-score × 25, kanal tamponu" },
      { l: "RIVER", v: "HST + yüzdelik kalibrasyon" },
    ]},
  { id: "decision", num: "04", title: "KARAR MOTORU", sub: "TEK DİNAMİK EŞİK",
    color: "#FF3366", icon: "⚡",
    desc: "Üç kademeli sınıflandırma yoktur. is_anomaly ve uplink_eligible aynı koşuldur: skor ≥ eşik. Eşik bataryaya ve RL düzeltmesine göre 40–85 arasında hareket eder.",
    detail: "Batarya > %50 → taban 50; %20–50 → 60; < %20 → 70. RL −5 / 0 / +5 ekler; sonuç max(40, min(85, …)). Eşiğin altı DROP, üstü uplink + orbiter kuyruğuna yazılır.",
    metrics: [
      { l: "TABAN (dolu batarya)", v: "50" },
      { l: "ARALIK", v: "40 — 85" },
      { l: "KARAR", v: "skor ≥ eşik → TX" },
    ]},
  { id: "priority", num: "05", title: "ÖNCELİKLENDİRME", sub: "BİLİMSEL SINIFLANDIRMA",
    color: "#FF00FF", icon: "🏷️",
    desc: "Anomali tespit edilen veriler bilimsel önemlerine göre sınıflandırılır. Birden fazla sensör aynı anda anomali gösteriyorsa 'organik molekül imzası' olarak en yüksek öncelik atanır.",
    detail: "Organik Molekül İmzası (3+ sensör aynı anda) → 10/10 | Metan Spike (CH₄) → 8/10 | Spektral Sapma (SPEC) → 7/10 | Nem Anomalisi (MOIST) → 6/10 | Radyasyon (UV) → 5/10 | Atmosferik (O₂, CO₂) → 5/10 | Basınç (PRESS) → 4/10 | Sıcaklık (TEMP) → 4/10",
    metrics: [
      { l: "EN YÜKSEK", v: "Organik Molekül — 10/10" },
      { l: "SEVİYELER", v: "KRİTİK / YÜKSEK / ORTA / DÜŞÜK" },
      { l: "SINIFLANDIRMA", v: "8 anomali tipi" },
    ]},
  { id: "compress", num: "06", title: "SIKIŞTIRMA & FİLTRELEME", sub: "DELTA + DEFLATE + FİLTRE",
    color: "#00FF88", icon: "🗜️",
    desc: "Önce anomali skoruna göre paket seçimi (yüksek skorlu veriler iletim kuyruğuna alınır). Uplink yükü, float64 akış üzerinde delta kodlama ile ardından zlib (DEFLATE) sıkıştırmasıyla küçültülür; böylece DSN üzerinde hem filtre hem de gerçek ikili sıkıştırma kazancı elde edilir.",
    detail: "Backend: her iletim partisinde raw_value ve anomaly_score çiftleri little-endian float64 olarak paketlenir → ardışık örnek farkları (delta encode) → zlib.compress (seviye enerjiye göre 6–9). Filtre eşiğin altını düşürür; eşik sabit 50 değildir. İletim analizi sayfasında byte tabanlı DEFLATE oranı stats_update ile gelir.",
    metrics: [
      { l: "ALGORİTMA", v: "Delta + zlib DEFLATE" },
      { l: "FİLTRE", v: "skor < eşik → DROP" },
      { l: "PAKET (sim.)", v: "256 byte / paket" },
    ]},
  { id: "transmit", num: "07", title: "DSN İLETİMİ", sub: "DEEP SPACE NETWORK",
    color: "#00F2FF", icon: "🛰️",
    desc: "Filtrelenen veriler NASA Deep Space Network (DSN) üzerinden Dünya'ya iletilir. 3 istasyon (Goldstone, Canberra, Madrid) 120° aralıklarla yerleştirilmiş olup 7/24 kapsama sağlar. Tek yön gecikme 4-24 dakikadır.",
    detail: "X-band direkt anten: ~3 kbps (34m DSN anteni). UHF orbiter relay (MRO, MAVEN): ~2 Mbps. Günlük iletim penceresi: 4-5 geçiş/sol, toplam ~1 Gbit kapasite. Store-and-forward protokolü: DTN (Delay-Tolerant Networking) ile paketler güvenle saklanıp iletişim penceresi açılınca gönderilir.",
    metrics: [
      { l: "GECİKME", v: "4-24 dakika (tek yön)" },
      { l: "KAPASİTE", v: "~1 Gbit/sol" },
      { l: "İSTASYONLAR", v: "Goldstone, Canberra, Madrid" },
    ]},
  { id: "ground", num: "08", title: "YER İSTASYONU", sub: "REASSEMBLY & DASHBOARD",
    color: "#FF00FF", icon: "🖥️",
    desc: "Dünya'ya ulaşan paketler yer istasyonunda birleştirilir (reassembly), dekode edilir ve veritabanına yazılır. WebSocket üzerinden gerçek zamanlı olarak dashboard'a aktarılır. Bilim insanları anomalileri inceleyip onaylar.",
    detail: "Paket reassembly → PostgreSQL veritabanına kayıt → FastAPI REST API ile erişim → WebSocket broadcast ile React dashboard'a canlı aktarım → Bilim insanları anomalileri inceler ve onaylar → Veriler PDS (Planetary Data System) formatında arşivlenir.",
    metrics: [
      { l: "VERİTABANI", v: "PostgreSQL (async)" },
      { l: "CANLI_YAYIN", v: "WebSocket yayını" },
      { l: "ÖN_YÜZ", v: "React 18 + Recharts" },
    ]},
];

const BASE_STEP_MS = 3000;

const SPEED_PRESETS = [
  { id: "slow", label: "YAVAŞ", mult: 0.55 },
  { id: "normal", label: "NORMAL", mult: 1 },
  { id: "fast", label: "HIZLI", mult: 1.65 },
];

function PipelineCanvas({ running, step, speedMult }) {
  const ref = useRef(null);
  const anim = useRef(null);
  const particles = useRef([]);
  const speedRef = useRef(speedMult);
  speedRef.current = speedMult;
  // running/step ref üzerinden okunur; efektin bağımlılığı olsalardı her adım
  // değişiminde canvas ve animasyon döngüsü baştan kurulur, akış takılırdı.
  const runningRef = useRef(running);
  runningRef.current = running;
  const stepRef = useRef(step);
  stepRef.current = step;

  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");

    let w = 0;
    let h = 0;
    let nodeY = 0;
    let nodes = [];

    function layout() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = c.offsetWidth;
      h = c.offsetHeight;
      if (w === 0 || h === 0) return;
      c.width = w * dpr;
      c.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      nodeY = h / 2;
      nodes = STEPS.map((_, i) => ({
        x: 50 + (i * (w - 100)) / (STEPS.length - 1),
        y: nodeY,
      }));
    }

    layout();

    const observer = new ResizeObserver(layout);
    observer.observe(c);

    function spawn() {
      const anom = Math.random() < 0.15;
      const sm = speedRef.current;
      particles.current.push({
        x: nodes[0].x, y: nodeY + (Math.random() - 0.5) * 20,
        seg: 0, prog: 0,
        spd: (0.0018 + Math.random() * 0.0016) * sm,
        color: anom ? "#FF3366" : "#00F2FF",
        anom, sz: anom ? 4.5 : 3, alive: true, opacity: 1,
        trail: [],
      });
    }

    function draw() {
      if (nodes.length === 0) {
        anim.current = requestAnimationFrame(draw);
        return;
      }
      const step = stepRef.current;
      ctx.clearRect(0, 0, w, h);

      // Connection lines with gradient
      for (let i = 0; i < nodes.length - 1; i++) {
        const from = nodes[i], to = nodes[i + 1];
        const grad = ctx.createLinearGradient(from.x, 0, to.x, 0);
        grad.addColorStop(0, `${STEPS[i].color}20`);
        grad.addColorStop(1, `${STEPS[i + 1].color}20`);
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Node circles
      nodes.forEach((pos, i) => {
        const s = STEPS[i];
        const glow = i === step;

        if (glow) {
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 22, 0, Math.PI * 2);
          ctx.strokeStyle = `${s.color}15`;
          ctx.lineWidth = 2;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 16, 0, Math.PI * 2);
          ctx.strokeStyle = `${s.color}30`;
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, glow ? 10 : 7, 0, Math.PI * 2);
        ctx.fillStyle = glow ? s.color : `${s.color}60`;
        ctx.shadowColor = glow ? s.color : "transparent";
        ctx.shadowBlur = glow ? 16 : 0;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Node label
        ctx.font = `bold ${glow ? 10 : 8}px JetBrains Mono`;
        ctx.fillStyle = glow ? s.color : "#506070";
        ctx.textAlign = "center";
        ctx.fillText(s.num, pos.x, pos.y + 30);
      });

      // Particles
      particles.current.forEach(p => {
        if (!p.alive) return;
        const from = nodes[p.seg];
        const to = nodes[Math.min(p.seg + 1, nodes.length - 1)];

        p.prog += p.spd;
        if (p.prog >= 1) {
          p.seg++;
          p.prog = 0;
          // Step 6 (index 5) = compression/filter — normal packets die here
          if (p.seg === 5 && !p.anom) {
            p.alive = false;
            // Fade out effect
            for (let t = 0; t < 6; t++) {
              const fx = p.x + (Math.random() - 0.5) * 12;
              const fy = p.y + (Math.random() - 0.5) * 12;
              ctx.beginPath();
              ctx.arc(fx, fy, 1.5, 0, Math.PI * 2);
              ctx.fillStyle = "#FF336640";
              ctx.fill();
            }
            return;
          }
          if (p.seg >= nodes.length - 1) {
            p.alive = false;
            // Arrival effect
            for (let t = 0; t < 8; t++) {
              const angle = (Math.PI * 2 * t) / 8;
              const fx = p.x + Math.cos(angle) * 10;
              const fy = p.y + Math.sin(angle) * 10;
              ctx.beginPath();
              ctx.arc(fx, fy, 1.5, 0, Math.PI * 2);
              ctx.fillStyle = "#00FF8850";
              ctx.fill();
            }
            return;
          }
        }

        p.x = from.x + (to.x - from.x) * p.prog;
        p.y = from.y + (to.y - from.y) * p.prog + Math.sin(p.prog * Math.PI * 2) * 6;

        // Trail
        p.trail.push({ x: p.x, y: p.y });
        if (p.trail.length > 8) p.trail.shift();
        p.trail.forEach((t, ti) => {
          const a = (ti / p.trail.length) * 0.3;
          ctx.beginPath();
          ctx.arc(t.x, t.y, p.sz * 0.5, 0, Math.PI * 2);
          ctx.fillStyle = p.color + Math.round(a * 255).toString(16).padStart(2, "0");
          ctx.fill();
        });

        // Main dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.sz, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      particles.current = particles.current.filter(p => p.alive);
      if (runningRef.current && Math.random() < 0.045 * speedRef.current) spawn();
      anim.current = requestAnimationFrame(draw);
    }
    draw();
    return () => {
      cancelAnimationFrame(anim.current);
      observer.disconnect();
    };
  }, []);

  return <canvas ref={ref} className="w-full h-32" />;
}

function LiveStats({ sim, stats }) {
  const [demo, setDemo] = useState({ total: 0, tx: 0, dropped: 0 });
  const hasLive = stats && (stats.total_packets ?? 0) > 0;

  useEffect(() => {
    if (!sim || hasLive) return;
    const t = setInterval(() => {
      setDemo(prev => {
        const anom = Math.random() < 0.15;
        return {
          total: prev.total + 1,
          tx: anom ? prev.tx + 1 : prev.tx,
          dropped: anom ? prev.dropped : prev.dropped + 1,
        };
      });
    }, 1600);
    return () => clearInterval(t);
  }, [sim, hasLive]);

  const total = hasLive ? (stats.total_packets ?? 0) : demo.total;
  const txRaw = hasLive ? (stats.transmitted_packets ?? 0) : demo.tx;
  const tx = hasLive ? Math.min(txRaw, Math.max(0, total)) : txRaw;
  const dropped = hasLive ? Math.max(0, total - tx) : demo.dropped;
  const filtPct = total > 0 ? ((dropped / total) * 100).toFixed(1) : "0";
  const dSave = hasLive
    ? Math.min(100, Math.max(0, Number(stats.payload_deflate_savings_percent) || 0))
    : 0;
  const bSave = hasLive
    ? Math.min(100, Math.max(0, Number(stats.bandwidth_saved_percent) || 0))
    : 0;
  const useDeflate = hasLive && dSave > 0;

  const rows = [
    { l: "İŞLENEN (paket)", v: total.toLocaleString("tr-TR"), c: "#00F2FF" },
    { l: "İLETİLEN", v: tx.toLocaleString("tr-TR"), c: "#FF00FF" },
    { l: "FİLTRE ORANI", v: `%${filtPct}`, c: "#FFAA00" },
    {
      l: useDeflate ? "DEFLATE TASARRUFU" : hasLive ? "BANT TASARRUFU" : "BANT TASARRUFU (sim.)",
      v: `%${useDeflate ? dSave.toFixed(1) : hasLive ? bSave.toFixed(1) : filtPct}`,
      c: "#00FF88",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {rows.map(m => (
        <div key={m.l} className="text-center p-3" style={{ background: "#050810", border: "1px solid #0D1520" }}>
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>{m.l}</p>
          <p className="text-xl font-extrabold mt-1" style={{ color: m.c, textShadow: `0 0 8px ${m.c}30` }}>{m.v}</p>
        </div>
      ))}
    </div>
  );
}

export default function PipelineAnimation({ stats }) {
  const [activeStep, setActiveStep] = useState(0);
  const [sim, setSim] = useState(true);
  const [curStep, setCurStep] = useState(0);
  const [speedIdx, setSpeedIdx] = useState(1);
  const [followActiveStep, setFollowActiveStep] = useState(true);

  const speedMult = SPEED_PRESETS[speedIdx].mult;
  const stepMs = Math.round(BASE_STEP_MS / speedMult);

  useEffect(() => {
    if (!sim) return;
    const t = setInterval(() => {
      setCurStep(p => (p + 1) % STEPS.length);
    }, stepMs);
    return () => clearInterval(t);
  }, [sim, stepMs]);

  useEffect(() => {
    if (sim && followActiveStep) setActiveStep(curStep);
  }, [curStep, sim, followActiveStep]);

  const progressPct = ((curStep + 1) / STEPS.length) * 100;

  const openStep = (idx) => {
    setFollowActiveStep(false);
    setActiveStep(prev => (prev === idx ? null : idx));
  };

  return (
    <div className="space-y-5">
      <div className="n-hud p-4" style={{ border: "1px solid #FFAA0045", background: "linear-gradient(135deg, #FFAA000A, #060910)" }}>
        <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#FFAA00" }}>Şeffaflık — gösterim / şema</p>
        <p className="text-xs mt-2 leading-relaxed" style={{ color: "#708090" }}>
          Bu sayfadaki animasyon ve adım metinleri <span style={{ color: "#99AAB8" }}>pedagojik şema</span> ve sahnelemedir; gerçek rover uçuş yazılımının birebir kopyası değildir. DSN süreleri ve kapasite ifadeleri genelleştirilmiştir. Edge kararları ve sayısal metrikler backend ile İletim Analizi sayfasındaki canlı veriye dayanır; istatistik kutularında canlı veri yoksa sayaçlar yerel demo sayaçları kullanılır.
        </p>
      </div>
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>
            UÇTAN UCA VERİ AKIŞ MİMARİSİ
          </p>
          <p className="text-sm mt-1" style={{ color: "#708090" }}>
            Mars rover sensör verisinin 8 katmanlı işleme sürecini adım adım gözlemleyin — her adım ~{(stepMs / 1000).toFixed(1)}s
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded overflow-hidden" style={{ border: "1px solid #1A2535" }}>
            {SPEED_PRESETS.map((p, i) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setSpeedIdx(i)}
                className="px-3 py-2 text-xs font-bold uppercase tracking-widest transition-all"
                style={{
                  background: i === speedIdx ? "#00F2FF18" : "#050810",
                  color: i === speedIdx ? "#00F2FF" : "#607080",
                  borderRight: i < SPEED_PRESETS.length - 1 ? "1px solid #1A2535" : "none",
                }}
              >
                {p.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setFollowActiveStep(true)}
            className="n-btn-primary text-xs py-2 px-3"
            style={{ opacity: followActiveStep ? 0.5 : 1 }}
          >
            AKTİF_ADIMI_TAKİP
          </button>
          <button onClick={() => setSim(!sim)} className={sim ? "n-btn-danger" : "n-btn-primary"}>
            {sim ? "DURDUR" : "BAŞLAT"}
          </button>
        </div>
      </div>

      {/* Progress */}
      <div>
        <div className="flex justify-between text-xs uppercase tracking-widest mb-1.5" style={{ color: "#506070" }}>
          <span>İş hattı ilerlemesi</span>
          <span style={{ color: "#00F2FF" }}>ADIM {String(curStep + 1).padStart(2, "0")} / {String(STEPS.length).padStart(2, "0")}</span>
        </div>
        <div className="h-2 rounded-full overflow-hidden" style={{ background: "#0D1520" }}>
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${progressPct}%`,
              background: "linear-gradient(90deg, #00F2FF, #FF00FF)",
              boxShadow: "0 0 12px #00F2FF50",
            }}
          />
        </div>
      </div>

      {/* Live stats */}
      <LiveStats sim={sim} stats={stats} />

      {/* Pipeline canvas */}
      <div className="n-hud p-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>CANLI PAKET AKIŞI</p>
          <div className="flex gap-5 text-xs uppercase tracking-wide" style={{ color: "#708090" }}>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ background: "#00F2FF", boxShadow: "0 0 6px #00F2FF60" }} /> NORMAL VERİ
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ background: "#FF3366", boxShadow: "0 0 6px #FF336660" }} /> ANOMALİ VERİ
            </span>
            <span style={{ color: "#506070" }}>Normal veri 6. adımda filtrelenir — sadece anomali Dünya'ya ulaşır</span>
          </div>
        </div>
        <PipelineCanvas running={sim} step={curStep} speedMult={speedMult} />
        <div className="flex justify-between mt-3 px-8">
          {STEPS.map((s, i) => (
            <button key={s.id} type="button" onClick={() => openStep(i)}
              className="text-center transition-all cursor-pointer group"
              style={{ maxWidth: "90px" }}>
              <span className="text-lg mb-1 block">{s.icon}</span>
              <span className="text-xs uppercase tracking-wide font-medium block leading-tight"
                style={{
                  color: i === curStep ? s.color : activeStep === i ? "#8899AA" : "#506070",
                  textShadow: i === curStep ? `0 0 8px ${s.color}40` : "none",
                }}>
                {s.sub}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Step detail cards */}
      <div className="space-y-2">
        {STEPS.map((step, idx) => {
          const isActive = activeStep === idx;
          const isCur = curStep === idx;
          return (
            <button key={step.id} type="button" onClick={() => openStep(idx)}
              className="w-full text-left transition-all duration-300"
              style={{
                background: isActive ? "#0A0F18" : "#060910",
                border: `1px solid ${isActive ? "#1A2535" : "#0D1520"}`,
                borderLeft: `3px solid ${isCur ? step.color : isActive ? step.color + "60" : "transparent"}`,
                boxShadow: isCur ? `inset 4px 0 16px ${step.color}12` : "none",
                padding: isActive ? "20px" : "16px",
              }}>
              <div className="flex items-center gap-5">
                <div className={`w-14 h-14 flex items-center justify-center text-xl shrink-0 ${isCur ? "animate-float" : ""}`}
                  style={{ background: `${step.color}10`, border: `1px solid ${step.color}25` }}>
                  {step.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold px-2 py-0.5" style={{ background: `${step.color}15`, color: step.color }}>{step.num}</span>
                    <span className="text-sm font-bold" style={{ color: "#BCC8D4" }}>{step.title}</span>
                    {isCur && <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: step.color, boxShadow: `0 0 8px ${step.color}` }} />}
                    <span className="text-xs uppercase tracking-widest ml-auto" style={{ color: `${step.color}80` }}>{step.sub}</span>
                  </div>
                  {!isActive && (
                    <p className="text-xs mt-1.5 line-clamp-1" style={{ color: "#607080" }}>{step.desc.slice(0, 100)}...</p>
                  )}
                </div>
              </div>

              {isActive && (
                <div className="mt-5 pt-4 space-y-4 animate-slide-up" style={{ borderTop: `1px solid ${step.color}15` }}>
                  <p className="text-sm leading-relaxed" style={{ color: "#8899AA" }}>{step.desc}</p>

                  <div className="p-4" style={{ background: "#050810", border: `1px solid ${step.color}15` }}>
                    <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: step.color }}>TEKNİK DETAY</p>
                    <p className="text-sm leading-relaxed" style={{ color: "#99AAB8" }}>{step.detail}</p>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    {step.metrics.map(m => (
                      <div key={m.l} className="p-3" style={{ background: "#050810", border: "1px solid #0D1520" }}>
                        <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#506070" }}>{m.l}</p>
                        <p className="text-sm font-bold mt-1" style={{ color: "#BCC8D4" }}>{m.v}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
