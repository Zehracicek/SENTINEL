import { motion } from "framer-motion";

function buildWavePoints(index) {
  const parts = [];
  const base = index * 2.1;
  for (let i = 0; i <= 100; i++) {
    const x = (i / 100) * 400;
    const y =
      52 +
      Math.sin(i * 0.14 + base) * 18 +
      Math.sin(i * 0.05 + base * 0.7) * 12 +
      Math.sin(i * 0.31 + index) * 6;
    parts.push(`${x},${y}`);
  }
  return parts.join(" ");
}

/** Telemetri film şeridi — simüle HUD / spektrum (koyu gradient tek başına boş görünmesin diye) */
export default function InstrumentStripViz({ tone, index }) {
  const n = 40;
  const bars = Array.from({ length: n }, (_, j) => ({
    key: j,
    dur: 1.6 + ((j + index * 3) % 7) * 0.22,
    delay: j * 0.04 + index * 0.12,
    w: 8 + (j % 5) * 3,
  }));

  const wavePts = buildWavePoints(index);
  const gradId = `inst-grad-${index}`;

  return (
    <div className="pointer-events-none absolute inset-[9%_5%] z-[8] overflow-hidden rounded-md border border-[#0D1520] bg-[#060910]/95 shadow-[inset_0_0_0_1px_rgba(0,242,255,0.06)]">
      <div
        className="absolute inset-0 opacity-[0.2]"
        style={{
          backgroundImage: `
            linear-gradient(90deg, ${tone}55 1px, transparent 1px),
            linear-gradient(0deg, ${tone}33 1px, transparent 1px)
          `,
          backgroundSize: "28px 28px",
        }}
      />

      <svg
        className="absolute inset-x-0 top-[10%] h-[40%] w-full opacity-90"
        viewBox="0 0 400 100"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={tone} stopOpacity="0.35" />
            <stop offset="100%" stopColor={tone} stopOpacity="0" />
          </linearGradient>
        </defs>
        <motion.polyline
          fill={`url(#${gradId})`}
          stroke={tone}
          strokeWidth="1.4"
          strokeOpacity={0.75}
          points={`0,100 ${wavePts} 400,100`}
          initial={{ opacity: 0.5 }}
          animate={{ opacity: [0.5, 1, 0.55] }}
          transition={{
            duration: 3.2 + index * 0.2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.polyline
          fill="none"
          stroke={tone}
          strokeWidth="1.2"
          strokeOpacity={0.9}
          points={wavePts}
          animate={{ opacity: [0.65, 1, 0.7] }}
          transition={{
            duration: 2.4 + index * 0.15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </svg>

      <div className="absolute inset-x-3 bottom-[18%] top-[48%] flex items-end justify-between gap-[3px]">
        {bars.map((b) => (
          <motion.div
            key={b.key}
            className="min-h-[6px] flex-1 rounded-[1px]"
            style={{
              backgroundColor: tone,
              maxWidth: b.w,
              boxShadow: `0 0 10px ${tone}55`,
            }}
            animate={{
              height: [
                `${12 + ((b.key + index) % 8) * 4}%`,
                `${55 + ((b.key * 2 + index) % 12) * 3}%`,
                `${18 + (b.key % 10) * 3}%`,
              ],
              opacity: [0.4, 0.9, 0.45],
            }}
            transition={{
              duration: b.dur,
              repeat: Infinity,
              ease: "easeInOut",
              delay: b.delay,
            }}
          />
        ))}
      </div>

      <motion.div
        className="absolute inset-x-0 h-[12%] bg-gradient-to-b from-transparent via-white/15 to-transparent"
        initial={{ top: "-12%" }}
        animate={{ top: "100%" }}
        transition={{
          duration: 5.5 + index * 0.4,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      <div className="absolute left-3 top-3 flex gap-2 font-mono text-[8px] uppercase tracking-wider text-white/40">
        <span style={{ color: tone }}>CANLI</span>
        <span>12 KANAL</span>
        <span className="text-white/25">|</span>
        <span>50 Hz</span>
      </div>
    </div>
  );
}
