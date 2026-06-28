import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Warm-ink ground — deliberately off the cold GitHub-dark default.
        bg: "#0e0f13",
        surface: "#15171c",
        "surface-hover": "#1b1e24",
        border: "#272b33",
        "border-strong": "#363b45",
        // Warm paper-tone text for ledger gravitas.
        text: "#e9e7e2",
        muted: "#8b8f99",
        faint: "#5b5e67",
        // Single signal: amber = flagged. The system raising a hand, not "good".
        accent: "#e0a24a",
        "accent-dim": "rgba(224,162,74,0.10)",
        "accent-soft": "rgba(224,162,74,0.42)",
        // Sober slate-cyan for methodological notes (the causal caveat register).
        note: "#6e93a6",
        "note-dim": "rgba(110,147,166,0.10)",
        good: "#7faa72",
        warn: "#6e93a6",
        // Red is reserved for true errors only.
        bad: "#e5484d",
      },
      fontFamily: {
        display: ["var(--font-display)", "var(--font-sans)", "system-ui", "sans-serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      maxWidth: { shell: "1320px" },
      keyframes: {
        "rise-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "draw-in": {
          "0%": { opacity: "0", transform: "scaleX(0.85)" },
          "100%": { opacity: "1", transform: "scaleX(1)" },
        },
      },
      animation: {
        "rise-in": "rise-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
        "draw-in": "draw-in 0.6s cubic-bezier(0.22, 1, 0.36, 1) both",
      },
    },
  },
  plugins: [],
};

export default config;
