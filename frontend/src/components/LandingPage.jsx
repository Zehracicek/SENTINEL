import {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
import {
  AnimatePresence,
  motion,
  useMotionValueEvent,
  useScroll,
  useSpring,
  useTransform,
} from "framer-motion";
import {
  Activity,
  ChevronDown,
  CloudCog,
  GitBranch,
  Layers,
  ListOrdered,
  Package,
  Radio,
  Satellite,
  Scale,
  Server,
  ShieldAlert,
  Sparkles,
  Zap,
} from "lucide-react";
import { LANDING_FLOW_STEPS, LANDING_AI_BLOCK } from "../data/landingFlow";
import InstrumentStripViz from "./landing/InstrumentStripViz";
import CanvasErrorBoundary from "./landing/CanvasErrorBoundary";

const LandingRoverCanvas = lazy(() =>
  import("./landing/LandingRoverCanvas"),
);
const HyperdrivePanel = lazy(() =>
  import("./landing/MarsSimPanels").then((m) => ({
    default: m.HyperdrivePanel,
  })),
);
const CaspianPanel = lazy(() =>
  import("./landing/MarsSimPanels").then((m) => ({
    default: m.CaspianPanel,
  })),
);

const STEP_ICONS = {
  collect: Satellite,
  buffer: Layers,
  anomaly: ShieldAlert,
  decision: Scale,
  priority: ListOrdered,
  compress: Package,
  transmit: Radio,
  ground: Server,
};

const AI_ICONS = {
  activity: Activity,
  "git-branch": GitBranch,
  zap: Zap,
  "cloud-cog": CloudCog,
  sparkles: Sparkles,
};

const MARQUEE_SEGMENTS = [
  "EDGE İŞLEM",
  "MSL 12 KANAL",
  "SSR TAMPON",
  "Z-SCORE + RIVER",
  "UPLINK KUYRUĞU",
  "DELTA + DEFLATE",
  "DSN MODELİ",
  "WEBSOCKET",
  "POSTGRES",
  "VERİ_AKIŞI",
];

const INSTRUMENT_FRAMES = [
  { label: "ÖN TELEMETRİ", sub: "Sol 001 · normalize okuma", tone: "#00F2FF" },
  { label: "YAN SSR", sub: "Ring buffer · öncelik sırası", tone: "#FF00FF" },
  { label: "ANOMALİ GÖRÜNÜMÜ", sub: "Hibrit skor 0–100", tone: "#FFAA00" },
  { label: "UPLINK ÖNİZLEME", sub: "Tek dinamik eşik", tone: "#FF3366" },
  { label: "DSN ZAMAN ÇİZGİSİ", sub: "Gecikme + drain", tone: "#00B8D4" },
  { label: "YER PANELİ", sub: "REST + WS", tone: "#8899AA" },
];

const PULL_QUOTES = [
  {
    text:
      "Gecikmeli bağlantıda her paket bir karar: tampon, skor ve uplink sırası aynı anda doğru olmalı.",
    cite: "SENTİNEL veri hattı özeti",
  },
  {
    text:
      "Yapay zekâ katmanı anomali ile karar motoru arasında; yer istasyonu eşik önerisi ve rover düşünce ile kapanır.",
    cite: "Akış konumu 03 → 04",
  },
];

const easeOut = [0.22, 1, 0.36, 1];

const fadeUp = {
  hidden: { opacity: 0, y: 48 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.75, delay: i * 0.06, ease: easeOut },
  }),
};

const stagger = {
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.08 } },
};

function useScrollSpy(stepRefs, aiRef, sectionIds) {
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [aiActive, setAiActive] = useState(false);
  const [railIndex, setRailIndex] = useState(0);

  useEffect(() => {
    const measure = () => {
      const mid = window.innerHeight * 0.44;
      let aiOn = false;
      if (aiRef.current) {
        const r = aiRef.current.getBoundingClientRect();
        aiOn = r.top < mid && r.bottom > mid;
      }
      setAiActive(aiOn);
      if (aiOn) {
        setActiveStepIndex(-1);
      } else {
        let best = 0;
        let bestDist = Infinity;
        stepRefs.current.forEach((el, i) => {
          if (!el) return;
          const r = el.getBoundingClientRect();
          if (r.bottom < 120 || r.top > window.innerHeight - 120) return;
          const c = (r.top + r.bottom) / 2;
          const d = Math.abs(c - mid);
          if (d < bestDist) {
            bestDist = d;
            best = i;
          }
        });
        setActiveStepIndex(best);
      }

      let bestR = 0;
      let bestRD = Infinity;
      sectionIds.forEach((id, i) => {
        const el = document.getElementById(id);
        if (!el) return;
        const r = el.getBoundingClientRect();
        if (r.bottom < 40 || r.top > window.innerHeight - 40) return;
        const c = (r.top + r.bottom) / 2;
        const d = Math.abs(c - mid);
        if (d < bestRD) {
          bestRD = d;
          bestR = i;
        }
      });
      setRailIndex(bestR);
    };
    measure();
    window.addEventListener("scroll", measure, { passive: true });
    window.addEventListener("resize", measure);
    return () => {
      window.removeEventListener("scroll", measure);
      window.removeEventListener("resize", measure);
    };
  }, [aiRef, stepRefs, sectionIds]);

  return { activeStepIndex, aiActive, railIndex };
}

function ProgressRail({ ids, labels, activeVisualIndex }) {
  const scrollToId = (id) => {
    const el = document.getElementById(id);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <motion.nav
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.5, duration: 0.6, ease: easeOut }}
      className="pointer-events-auto fixed left-3 top-1/2 z-40 hidden -translate-y-1/2 flex-col gap-2 xl:left-6 xl:flex"
      aria-label="Bölüm atlama"
    >
      {ids.map((id, i) => (
        <button
          key={id}
          type="button"
          onClick={() => scrollToId(id)}
          className="group flex items-center gap-2 rounded-full py-1 pl-1 pr-2 text-left transition hover:bg-[#00F2FF]/08"
          title={labels[i]}
        >
          <span
            className={`h-2 w-2 rounded-full transition ${
              activeVisualIndex === i
                ? "scale-125 bg-[#00F2FF] shadow-[0_0_14px_rgba(0,242,255,0.45)]"
                : "bg-[#0D1520] group-hover:bg-[#506070]"
            }`}
          />
          <span className="max-w-[7rem] truncate font-mono text-[9px] uppercase tracking-widest text-[#506070] opacity-0 transition group-hover:opacity-100">
            {labels[i]}
          </span>
        </button>
      ))}
    </motion.nav>
  );
}

const RAIL_IDS = [
  "mars-hero",
  "mars-marquee",
  "mars-instruments",
  "mars-hyperdrive",
  "mars-caspian",
  "mars-story",
  ...LANDING_FLOW_STEPS.map((s) => `adim-${s.id}`),
  "mars-ai",
  "mars-quotes",
  "mars-cta",
];

const RAIL_LABELS = [
  "Giriş",
  "Şerit",
  "Kanallar",
  "Hyperdrive",
  "Caspian",
  "Hikâye",
  ...LANDING_FLOW_STEPS.map((s) => s.title),
  "YZ katmanı",
  "Alıntılar",
  "Panel",
];

export default function LandingPage() {
  const stepRefs = useRef([]);
  const aiRef = useRef(null);
  const roverProgressRef = useRef(0);
  const { activeStepIndex, aiActive, railIndex } = useScrollSpy(
    stepRefs,
    aiRef,
    RAIL_IDS,
  );
  const [expandedId, setExpandedId] = useState(null);

  const { scrollYProgress } = useScroll();
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 64,
    damping: 28,
    mass: 0.9,
  });

  useMotionValueEvent(smoothProgress, "change", (v) => {
    roverProgressRef.current = v;
  });
  useLayoutEffect(() => {
    roverProgressRef.current = smoothProgress.get();
  }, [smoothProgress]);

  const heroOpacity = useTransform(smoothProgress, [0, 0.14], [1, 0]);
  const heroY = useTransform(smoothProgress, [0, 0.16], [0, -120]);
  const heroScale = useTransform(smoothProgress, [0, 0.14], [1, 0.94]);

  const setStepRef = useCallback((i) => (el) => {
    stepRefs.current[i] = el;
  }, []);

  const heroLine1 = "Sekiz adımlı uçtan uca veri hattı";
  const heroWords = heroLine1.split(" ");

  return (
    <div
      className="relative min-h-screen overflow-x-hidden font-sans antialiased selection:bg-[#00F2FF]/20 selection:text-[#E8EEF4]"
      style={{
        background: "#04060A",
        color: "#BCC8D4",
      }}
    >
      <CanvasErrorBoundary>
        <Suspense fallback={null}>
          <LandingRoverCanvas progressRef={roverProgressRef} />
        </Suspense>
      </CanvasErrorBoundary>

      <div
        className="pointer-events-none fixed inset-0 z-[1] bg-gradient-to-b from-black/75 via-black/20 via-40% to-black/88"
        aria-hidden
      />
      <div className="landing-grain z-[2]" aria-hidden />

      <ProgressRail
        ids={RAIL_IDS}
        labels={RAIL_LABELS}
        activeVisualIndex={railIndex}
      />

      <motion.header
        initial={{ y: -24, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.75, ease: easeOut }}
        className="sticky top-0 z-40"
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#00F2FF]/45 to-transparent" />
        <div className="border-b border-[#0D1520] bg-[#060910]/90 shadow-[0_8px_32px_-12px_rgba(0,0,0,0.75)] backdrop-blur-2xl backdrop-saturate-150">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-3.5 sm:px-8 sm:py-4">
            <Link
              to="/"
              className="group flex min-w-0 items-center gap-3.5 sm:gap-4"
            >
              <div className="relative flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-[#00F2FF]/35 bg-gradient-to-br from-[#00F2FF]/12 to-[#080C14] shadow-[inset_0_1px_0_rgba(0,242,255,0.12)] sm:h-11 sm:w-11">
                <span
                  className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                  style={{
                    background:
                      "radial-gradient(120% 80% at 30% 20%, rgba(0,242,255,0.2), transparent 55%)",
                  }}
                />
                <span
                  className="absolute bottom-0 left-1/2 h-8 w-px -translate-x-1/2 rounded-full opacity-70"
                  style={{
                    background:
                      "linear-gradient(180deg, transparent, #00F2FF, #FF00FF)",
                  }}
                />
                <span className="relative font-editorial text-xl font-semibold leading-none text-[#E8EEF4] sm:text-[1.35rem]">
                  S
                </span>
              </div>
              <div className="min-w-0 text-left">
                <p className="font-mono text-[9px] font-medium uppercase tracking-[0.42em] text-[#607080] sm:text-[10px]">
                  SENTİNEL
                </p>
                <p className="truncate font-editorial text-lg font-semibold leading-tight tracking-tight text-[#E8EEF4] sm:text-xl">
                  Operasyon özeti
                </p>
              </div>
            </Link>

            <nav
              className="flex shrink-0 items-center gap-1 rounded-full border border-[#0D1520] bg-[#080C14]/95 p-1 shadow-[inset_0_1px_0_rgba(0,242,255,0.06)] backdrop-blur-md"
              aria-label="Ana gezinme"
            >
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Link
                  to="/veri_akisi"
                  className="block rounded-full px-3.5 py-2.5 font-mono text-[9px] font-semibold uppercase tracking-[0.22em] text-[#8899AA] transition-colors hover:bg-[#00F2FF]/10 hover:text-[#00F2FF] sm:px-4 sm:text-[10px]"
                >
                  Veri akışı
                </Link>
              </motion.div>
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                <Link
                  to="/gosterge_paneli"
                  className="group/cta relative block overflow-hidden rounded-full px-4 py-2.5 font-mono text-[9px] font-bold uppercase tracking-[0.18em] text-[#04060A] shadow-[0_0_28px_-6px_rgba(0,242,255,0.4)] transition-[filter,box-shadow] duration-300 hover:shadow-[0_0_40px_-4px_rgba(0,242,255,0.55)] hover:brightness-[1.06] sm:px-5 sm:text-[10px]"
                  style={{
                    background:
                      "linear-gradient(135deg, #7ee8ff 0%, #00F2FF 42%, #0099b8 100%)",
                  }}
                >
                  <span className="pointer-events-none absolute -left-1/2 top-0 h-full w-1/2 skew-x-12 bg-gradient-to-r from-transparent via-white/40 to-transparent opacity-0 transition-all duration-500 ease-out group-hover/cta:left-full group-hover/cta:opacity-100" />
                  <span className="relative">Panele gir</span>
                </Link>
              </motion.div>
            </nav>
          </div>
        </div>
      </motion.header>

      <section
        id="mars-hero"
        className="relative z-10 flex min-h-[100svh] flex-col justify-center px-5 pb-16 pt-8 sm:px-8"
      >
        <motion.div
          style={{ opacity: heroOpacity, y: heroY, scale: heroScale }}
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_20%,rgba(0,242,255,0.07),transparent_50%)]"
        />

        <div className="relative mx-auto w-full max-w-5xl text-center">
          <motion.p
            initial={{ opacity: 0, letterSpacing: "0.5em" }}
            animate={{ opacity: 1, letterSpacing: "0.28em" }}
            transition={{ duration: 1.1, ease: easeOut }}
            className="mb-6 font-mono text-[10px] font-semibold uppercase text-[#607080]"
          >
            Astrobiyolojik sensör · uç işlem · yer istasyonu
          </motion.p>

          <motion.h1
            className="font-editorial text-[clamp(2.1rem,6.5vw,4.25rem)] font-semibold leading-[0.95] tracking-tight text-[#E8EEF4] [text-shadow:0_4px_48px_rgba(0,0,0,0.9),0_0_40px_rgba(0,242,255,0.08)]"
            style={{ opacity: heroOpacity, y: heroY, scale: heroScale }}
          >
            <span className="block overflow-hidden">
              {heroWords.map((w, i) => (
                <motion.span
                  key={`${w}-${i}`}
                  initial={{ y: "100%", opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{
                    delay: 0.12 + i * 0.055,
                    duration: 0.65,
                    ease: easeOut,
                  }}
                  className="inline-block pr-[0.18em]"
                >
                  {w}
                </motion.span>
              ))}
            </span>
            <motion.span
              initial={{ opacity: 0, y: 28 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.85, duration: 0.8, ease: easeOut }}
              className="mt-4 block font-editorial text-[clamp(1.15rem,3.2vw,1.85rem)] font-normal italic text-[#00F2FF]/95"
              style={{ opacity: heroOpacity }}
            >
              gecikmeli bağlantıda güvenle iletim
            </motion.span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.15, duration: 0.8 }}
            className="mx-auto mt-8 max-w-2xl font-mono text-sm leading-relaxed text-[#708090]"
            style={{ opacity: heroOpacity }}
          >
            Bu sayfa, gösterge panelindeki sekiz adımı ve yapay zekâ katmanını — Mars hikâyesi
            tarzında kaydırma, marş ve yapışkan 3D ile anlatır.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.35, duration: 0.65, ease: easeOut }}
            className="mt-10 flex flex-wrap justify-center gap-3"
            style={{ opacity: heroOpacity }}
          >
            <Link
              to="/gosterge_paneli"
              className="inline-flex items-center justify-center rounded-full px-8 py-3.5 text-xs font-bold uppercase tracking-wider text-[#04060A] shadow-lg shadow-[0_0_24px_rgba(0,242,255,0.25)]"
              style={{
                background: "linear-gradient(135deg,#7ee8ff,#00F2FF)",
              }}
            >
              Canlı panele geç
            </Link>
            <motion.a
              href="#mars-story"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex items-center justify-center rounded-full border border-[#0D1520] px-8 py-3.5 text-xs font-semibold uppercase tracking-wider text-[#BCC8D4] hover:border-[#00F2FF]/45 hover:bg-[#00F2FF]/06"
            >
              Hikâyeyi kaydır
            </motion.a>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.6, duration: 0.6 }}
            className="mt-14 font-mono text-[10px] uppercase tracking-[0.35em] text-[#3A4A5C]"
          >
            Edge → AI → Dünya
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8, duration: 0.8 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          style={{ opacity: heroOpacity }}
        >
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
            className="flex flex-col items-center gap-1 text-[#506070]"
          >
            <span className="font-mono text-[9px] uppercase tracking-widest">
              Kaydır
            </span>
            <ChevronDown className="h-5 w-5 opacity-60" strokeWidth={1.5} />
          </motion.div>
        </motion.div>
      </section>

      <div
        id="mars-marquee"
        className="relative z-10 border-y border-[#0D1520] bg-[#060910]/80 py-3 backdrop-blur-[2px]"
      >
        <div className="overflow-hidden">
          <div className="flex w-max animate-landing-marquee font-mono text-[10px] font-medium uppercase tracking-[0.35em] text-[#506070]">
            {[...MARQUEE_SEGMENTS, ...MARQUEE_SEGMENTS].map((t, i) => (
              <span key={`${t}-${i}`} className="px-10">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      <section
        id="mars-instruments"
        className="relative z-10 border-b border-white/[0.05] py-16 sm:py-24"
      >
        <div className="px-5 sm:px-10">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-12%" }}
            variants={stagger}
            className="mx-auto mb-10 max-w-3xl text-center sm:text-left"
          >
            <motion.p
              variants={fadeUp}
              custom={0}
              className="font-mono text-[10px] font-semibold uppercase tracking-[0.35em] text-[#607080]"
            >
              Çoklu kanal önizleme
            </motion.p>
            <motion.h2
              variants={fadeUp}
              custom={1}
              className="font-editorial text-[clamp(1.75rem,4vw,2.75rem)] font-semibold leading-tight text-[#E8EEF4] [text-shadow:0_2px_32px_rgba(0,0,0,0.85)]"
            >
              Telemetri ve arayüz şeridi
            </motion.h2>
            <motion.p
              variants={fadeUp}
              custom={2}
              className="mt-3 font-mono text-xs leading-relaxed text-[#8899AA] sm:text-sm"
            >
              Tam genişlik film kareleri — her panel operasyon akışındaki bir görünümü temsil eder.
              Kaydırarak ilerleyin.
            </motion.p>
          </motion.div>
        </div>

        <div className="flex snap-x snap-mandatory gap-0 overflow-x-auto pb-4 [scrollbar-width:none] sm:gap-1 [&::-webkit-scrollbar]:hidden">
          {INSTRUMENT_FRAMES.map((f, i) => (
            <motion.div
              key={f.label}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true, margin: "-8%" }}
              transition={{ delay: i * 0.05, duration: 0.7, ease: easeOut }}
              className="relative h-[min(52vh,420px)] min-w-[min(92vw,920px)] flex-shrink-0 snap-center border-r border-[#0D1520] first:border-l first:border-[#0D1520]"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-[#060910] to-[#080C14]" />
              <motion.div
                className="absolute inset-0"
                style={{
                  background: `radial-gradient(ellipse 80% 60% at 30% 25%, ${f.tone}35, transparent 55%)`,
                }}
                animate={{ opacity: [0.5, 0.85, 0.5] }}
                transition={{
                  duration: 6 + i * 0.4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
              <InstrumentStripViz tone={f.tone} index={i} />
              <div className="pointer-events-none absolute inset-x-0 bottom-0 top-[42%] z-[12] bg-gradient-to-t from-black/95 via-black/45 to-transparent" />
              <div className="absolute left-6 top-6 z-[20] font-mono text-[10px] font-semibold uppercase tracking-[0.35em] text-white/90">
                {f.label}
              </div>
              <div className="absolute bottom-6 left-6 right-6 z-[20] max-w-lg">
                <p className="font-mono text-[11px] uppercase tracking-widest text-white/50">
                  SENTİNEL · simülasyon
                </p>
                <p className="mt-2 font-editorial text-xl text-[#E8EEF4] sm:text-2xl">
                  {f.sub}
                </p>
              </div>
              <div
                className="absolute right-6 top-6 z-[20] h-2 w-2 rounded-full"
                style={{
                  background: f.tone,
                  boxShadow: `0 0 16px ${f.tone}`,
                }}
              />
            </motion.div>
          ))}
        </div>
        <p className="px-5 pt-4 text-center font-mono text-[9px] uppercase tracking-[0.35em] text-[#3A4A5C] sm:px-10 sm:text-left">
          Yatay kaydır
        </p>
      </section>

      <CanvasErrorBoundary>
        <Suspense fallback={null}>
          <HyperdrivePanel />
        </Suspense>
      </CanvasErrorBoundary>
      <CanvasErrorBoundary>
        <Suspense fallback={null}>
          <CaspianPanel />
        </Suspense>
      </CanvasErrorBoundary>

      <main
        id="mars-story"
        className="relative z-10 mx-auto max-w-3xl px-5 py-20 sm:py-28"
      >
        <div className="min-w-0 space-y-4">
            <motion.div
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-10%" }}
              variants={stagger}
              className="mb-16 max-w-2xl"
            >
              <motion.p
                variants={fadeUp}
                custom={0}
                className="font-mono text-[10px] font-semibold uppercase tracking-[0.3em] text-[#607080]"
              >
                Uçtan uca hikâye
              </motion.p>
              <motion.h2
                variants={fadeUp}
                custom={1}
                className="font-editorial text-[clamp(1.85rem,4.5vw,3rem)] font-semibold leading-tight text-[#E8EEF4] [text-shadow:0_2px_28px_rgba(0,0,0,0.75)]"
              >
                Veriyi işleyin, sıraya alın, Dünya&apos;ya iletin
              </motion.h2>
              <motion.p
                variants={fadeUp}
                custom={2}
                className="mt-4 font-mono text-sm leading-relaxed text-[#8899AA]"
              >
                Sıra, paneldeki{" "}
                <strong className="font-semibold text-[#00F2FF]">VERİ_AKIŞI</strong>{" "}
                ekranı ile aynıdır. Arka plandaki{" "}
                <strong className="font-semibold text-[#FFAA00]">
                  NASA Perseverance
                </strong>{" "}
                modeli sayfa boyunca kaydırmayla döner ve kamera yörüngesi değişir.
              </motion.p>
            </motion.div>

            {LANDING_FLOW_STEPS.map((step, i) => {
              const Icon = STEP_ICONS[step.id] || Satellite;
              const open = expandedId === step.id;
              return (
                <motion.section
                  key={step.id}
                  id={`adim-${step.id}`}
                  ref={setStepRef(i)}
                  initial="hidden"
                  whileInView="show"
                  viewport={{ once: false, amount: 0.25, margin: "-8% 0px" }}
                  variants={{
                    hidden: { opacity: 0, y: 56 },
                    show: {
                      opacity: 1,
                      y: 0,
                      transition: { duration: 0.72, ease: easeOut },
                    },
                  }}
                  className="scroll-mt-28 border-b border-[#0D1520] py-16 first:pt-2"
                >
                  <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
                    <motion.div
                      layout
                      className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full border border-[#0D1520]"
                      style={{
                        background: `${step.color}14`,
                        boxShadow:
                          activeStepIndex === i
                            ? `0 0 24px ${step.color}44`
                            : "none",
                      }}
                      animate={{
                        scale: activeStepIndex === i ? 1.05 : 1,
                      }}
                      transition={{ type: "spring", stiffness: 320, damping: 22 }}
                    >
                      <Icon
                        className="h-5 w-5"
                        style={{ color: step.color }}
                        strokeWidth={1.35}
                      />
                    </motion.div>
                    <div className="min-w-0 flex-1">
                      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.28em] text-[#506070]">
                        Adım {String(i + 1).padStart(2, "0")} · {step.subtitle}
                      </p>
                      <h3 className="mt-1 font-editorial text-2xl font-semibold text-[#E8EEF4] sm:text-3xl">
                        {step.title}
                      </h3>
                      <p className="mt-3 font-mono text-sm leading-relaxed text-[#708090]">
                        {step.short}
                      </p>
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedId(open ? null : step.id)
                        }
                        className="mt-4 inline-flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wider text-[#00F2FF] hover:text-[#7ee8ff]"
                      >
                        {open ? "Detayı kapat" : "Teknik detay"}
                        <motion.span
                          animate={{ rotate: open ? 180 : 0 }}
                          transition={{ duration: 0.25 }}
                        >
                          <ChevronDown className="h-4 w-4" />
                        </motion.span>
                      </button>
                      <AnimatePresence initial={false}>
                        {open && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.35, ease: easeOut }}
                            className="overflow-hidden"
                          >
                            <p className="mt-4 border-l-2 border-[#00F2FF]/35 pl-4 font-mono text-sm leading-relaxed text-[#8899AA]">
                              {step.detail}
                            </p>
                          </motion.div>
                        )}
                      </AnimatePresence>
                      <Link
                        to={step.panelPath}
                        className="mt-5 inline-block font-mono text-xs font-semibold text-[#00F2FF] underline decoration-[#00F2FF]/35 underline-offset-4 hover:text-[#BCC8D4]"
                      >
                        {step.panelLabel} →
                      </Link>
                    </div>
                  </div>
                </motion.section>
              );
            })}

            <motion.article
              ref={aiRef}
              id="mars-ai"
              initial="hidden"
              whileInView="show"
              viewport={{ once: false, amount: 0.2 }}
              variants={{
                hidden: { opacity: 0, y: 64 },
                show: {
                  opacity: 1,
                  y: 0,
                  transition: { duration: 0.8, ease: easeOut },
                },
              }}
              className="relative scroll-mt-28 w-screen max-w-none border-y border-[#00F2FF]/22 bg-[#060910]/75 py-12 backdrop-blur-sm sm:py-16"
              style={{
                marginLeft: "calc(50% - 50vw)",
                marginRight: "calc(50% - 50vw)",
                boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
              }}
            >
              <motion.div
                className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full opacity-[0.15] blur-3xl"
                style={{ background: "#00F2FF" }}
                animate={{
                  scale: aiActive ? [1, 1.08, 1] : 1,
                  opacity: aiActive ? [0.12, 0.22, 0.12] : 0.12,
                }}
                transition={{ duration: 4, repeat: aiActive ? Infinity : 0 }}
              />
              <div className="relative mx-auto max-w-3xl px-5 sm:px-8">
                <p className="font-mono text-[10px] font-bold uppercase tracking-[0.35em] text-[#00F2FF]">
                  Akış 03 → 04 arası
                </p>
                <h3 className="mt-2 font-editorial text-2xl font-semibold text-[#E8EEF4] sm:text-3xl">
                  {LANDING_AI_BLOCK.title}
                </h3>
                <p className="mt-3 max-w-3xl font-mono text-sm leading-relaxed text-[#708090]">
                  {LANDING_AI_BLOCK.subtitle}
                </p>
                <motion.ul
                  initial="hidden"
                  whileInView="show"
                  viewport={{ once: true, margin: "-5%" }}
                  variants={stagger}
                  className="mt-8 grid gap-3 sm:grid-cols-2"
                >
                  {LANDING_AI_BLOCK.items.map((item) => {
                    const AI = AI_ICONS[item.icon] || Activity;
                    return (
                      <motion.li
                        key={item.head}
                        variants={fadeUp}
                        whileHover={{ y: -2, transition: { duration: 0.2 } }}
                        className="border border-[#0D1520] bg-[#080C14]/90 p-4"
                      >
                        <div className="mb-2 flex items-center gap-2 text-[#00F2FF]">
                          <AI className="h-4 w-4 shrink-0" strokeWidth={1.5} />
                          <p className="text-sm font-semibold">{item.head}</p>
                        </div>
                        <p className="font-mono text-xs leading-relaxed text-[#708090] sm:text-sm">
                          {item.text}
                        </p>
                      </motion.li>
                    );
                  })}
                </motion.ul>
                <div className="mt-8 flex flex-wrap gap-4">
                  <Link
                    to="/rover_zekasi"
                    className="font-mono text-xs font-semibold text-[#8899AA] underline decoration-[#00F2FF]/35 underline-offset-4 hover:text-[#E8EEF4]"
                  >
                    Rover zekâsı →
                  </Link>
                  <Link
                    to="/yer_istasyonu_bulut"
                    className="font-mono text-xs font-semibold text-[#8899AA] underline decoration-[#FF00FF]/35 underline-offset-4 hover:text-[#E8EEF4]"
                  >
                    Yer bulutu →
                  </Link>
                </div>
              </div>
            </motion.article>

            <section id="mars-quotes" className="space-y-20 py-24">
              {PULL_QUOTES.map((q) => (
                <motion.blockquote
                  key={q.cite}
                  initial={{ opacity: 0, scale: 0.94, y: 32 }}
                  whileInView={{ opacity: 1, scale: 1, y: 0 }}
                  viewport={{ once: false, amount: 0.35 }}
                  transition={{ duration: 0.75, ease: easeOut }}
                  className="mx-auto max-w-3xl border-l-2 border-[#00F2FF]/40 pl-6 sm:pl-10"
                >
                  <p className="font-editorial text-[clamp(1.35rem,3.6vw,2.1rem)] font-medium leading-snug text-[#BCC8D4]">
                    {q.text}
                  </p>
                  <footer className="mt-4 font-mono text-[10px] uppercase tracking-[0.25em] text-[#506070]">
                    — {q.cite}
                  </footer>
                </motion.blockquote>
              ))}
            </section>
        </div>

        <motion.footer
          id="mars-cta"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="relative z-10 mt-8 border-t border-[#0D1520] pt-14 pb-20 text-center"
        >
          <p className="font-mono text-xs text-[#506070]">
            SENTİNEL — eğitim ve simülasyon prototipi. Canlı Mars bağlantısı içermez.
          </p>
          <p className="mx-auto mt-3 max-w-lg font-mono text-[10px] leading-relaxed text-[#3A4A5C]">
            Perseverance 3B modeli NASA / JPL kaynaklıdır;{" "}
            <a
              href="https://science.nasa.gov/3d-resources/"
              className="text-[#607080] underline decoration-[#0D1520] underline-offset-2 hover:text-[#00F2FF]"
              target="_blank"
              rel="noreferrer"
            >
              NASA 3D Resources
            </a>{" "}
            kullanım koşullarına tabidir.
          </p>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="mt-6 inline-block">
            <Link
              to="/gosterge_paneli"
              className="inline-flex rounded-full border border-[#0D1520] px-8 py-3 font-mono text-xs font-bold uppercase tracking-wider text-[#E8EEF4] hover:border-[#00F2FF]/45 hover:bg-[#00F2FF]/08"
            >
              Operasyon paneline geç
            </Link>
          </motion.div>
        </motion.footer>
      </main>
    </div>
  );
}
