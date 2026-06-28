import type { Theme } from "@/components/ThemeProvider";

// Structural chart colours (grid, axes, tooltip chrome) that must flip with the
// theme. Recharts takes plain strings, not CSS classes, so these are resolved
// from the theme rather than Tailwind tokens.
export interface ChartTokens {
  grid: string;
  tick: string;
  axisLine: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
  tooltipLabel: string;
  cursor: string;
  accent: string;
}

export function chartTokens(theme: Theme): ChartTokens {
  if (theme === "light") {
    return {
      grid: "#e7e4dc",
      tick: "#5d616b",
      axisLine: "#d8d4ca",
      tooltipBg: "#ffffff",
      tooltipBorder: "#e4e1d9",
      tooltipText: "#1c1d22",
      tooltipLabel: "#5d616b",
      cursor: "rgba(169,110,21,0.08)",
      accent: "#a96e15",
    };
  }
  return {
    grid: "#22262d",
    tick: "#8b8f99",
    axisLine: "#272b33",
    tooltipBg: "#15171c",
    tooltipBorder: "#272b33",
    tooltipText: "#e9e7e2",
    tooltipLabel: "#8b8f99",
    cursor: "rgba(224,162,74,0.07)",
    accent: "#e0a24a",
  };
}

// Categorical race-series hues. Held constant across themes — they read on both
// paper and ink as filled bars, and keeping them stable preserves the legend's
// meaning when a reader switches themes.
export const RACE_SERIES: Record<string, string> = {
  White: "#6f93c0",
  Black: "#e0a24a",
  Hispanic: "#8fb56b",
  Asian: "#a98fd0",
};

// Single-series denial-by-race bar.
export const RACE_SINGLE = "#6f93c0";
