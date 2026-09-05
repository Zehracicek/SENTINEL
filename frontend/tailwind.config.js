/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    fontFamily: {
      mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      sans: ['"JetBrains Mono"', 'monospace'],
      editorial: ['"Cormorant Garamond"', 'Georgia', 'ui-serif', 'serif'],
    },
    extend: {
      colors: {
        n: {
          bg: "#0A0D12",
          panel: "#0E1219",
          "panel-2": "#131820",
          surface: "#1A1F2A",
          border: "#1E2533",
          "border-hi": "#2A3345",
          text: "#C8D0E0",
          "text-dim": "#5A6580",
          "text-dark": "#3A4560",
          cyan: "#00F2FF",
          "cyan-dim": "#00F2FF80",
          magenta: "#FF00FF",
          "magenta-dim": "#FF00FF60",
          purple: "#7000FF",
          "purple-dim": "#7000FF60",
          green: "#00FF88",
          yellow: "#FFAA00",
          red: "#FF3366",
          orange: "#FF8800",
        },
      },
      animation: {
        "pulse-n": "pulse-n 2s ease-in-out infinite",
        "glow": "glow 2s ease-in-out infinite",
        "blink": "blink 1s step-end infinite",
        "slide-up": "slideUp 0.3s ease-out",
        "scan": "scanLine 4s linear infinite",
        "critical": "critical 1.5s ease-in-out infinite",
        "landing-marquee": "marquee 42s linear infinite",
      },
      keyframes: {
        "pulse-n": {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        glow: {
          "0%,100%": { boxShadow: "0 0 4px var(--tw-shadow-color)" },
          "50%": { boxShadow: "0 0 16px var(--tw-shadow-color), 0 0 32px var(--tw-shadow-color)" },
        },
        blink: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        scanLine: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(500%)" },
        },
        critical: {
          "0%,100%": { borderColor: "#FF336660" },
          "50%": { borderColor: "#FF3366", boxShadow: "0 0 20px #FF336640" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
    },
  },
  plugins: [],
};
