"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTheme } from "./ThemeProvider";
import { chartTokens, RACE_SERIES, type ChartTokens } from "@/lib/chartTheme";

interface Row {
  income_band: string;
  race_group: string;
  n: number;
  n_denied: number;
  denial_rate: number;
}

const BAND_ORDER = ["under_50k", "50k_to_100k", "100k_to_150k", "150k_to_250k", "over_250k", "unknown"];
const RACE_FOCUS = ["White", "Black", "Hispanic", "Asian"];

// Human-readable band labels — the raw keys ("50k_to_100k") read as code.
const BAND_LABEL: Record<string, string> = {
  under_50k: "< $50k",
  "50k_to_100k": "$50–100k",
  "100k_to_150k": "$100–150k",
  "150k_to_250k": "$150–250k",
  over_250k: "> $250k",
  unknown: "Unknown",
};

// Minimum cell size before a denial rate is plotted. A band x race cell with a
// handful of applications can read 0% or 100% purely from sampling noise; an
// unsuppressed 100% bar looks broken even when it is technically correct.
// Below this n we drop the bar and label the cell small-n in the tooltip.
const MIN_N = 30;

// Categorical hues, decoupled from the semantic amber signal — distinct in both
// hue and lightness so the series stay separable. Shared with the legend/tooltip.
const palette = RACE_SERIES;

type ChartRow = { income_band: string } & Record<string, number | string | null>;

export function DenialByIncomeChart({ data }: { data: Row[] }) {
  const t = chartTokens(useTheme().theme);
  const pivot: Record<string, ChartRow> = {};
  for (const r of data) {
    if (!RACE_FOCUS.includes(r.race_group)) continue;
    pivot[r.income_band] ??= { income_band: r.income_band };
    // Suppress the rate for small-n cells, but keep n so the tooltip can show it.
    pivot[r.income_band][r.race_group] = r.n >= MIN_N ? r.denial_rate : null;
    pivot[r.income_band][`${r.race_group}__n`] = r.n;
  }
  const rows = BAND_ORDER.filter((b) => pivot[b]).map((b) => pivot[b]);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid stroke={t.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="income_band"
          stroke={t.tick}
          tick={{ fill: t.tick, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: t.axisLine }}
          tickFormatter={(v: string) => BAND_LABEL[v] ?? v}
        />
        <YAxis
          stroke={t.tick}
          tick={{ fill: t.tick, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: t.axisLine }}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
        />
        <Tooltip cursor={{ fill: t.cursor }} content={<IncomeTooltip tokens={t} />} />
        <Legend wrapperStyle={{ color: t.tick, fontSize: 11 }} />
        {RACE_FOCUS.map((g) => (
          <Bar key={g} dataKey={g} fill={palette[g]} radius={[2, 2, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function IncomeTooltip({ active, payload, label, tokens }: {
  active?: boolean;
  payload?: Array<{ payload: ChartRow }>;
  label?: string;
  tokens?: ChartTokens;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div
      style={{
        background: tokens?.tooltipBg ?? "#15171c",
        border: `1px solid ${tokens?.tooltipBorder ?? "#272b33"}`,
        borderRadius: 6,
        color: tokens?.tooltipText ?? "#e9e7e2",
        fontSize: 12,
        padding: "8px 10px",
      }}
    >
      <div style={{ color: tokens?.tooltipLabel ?? "#8b8f99", marginBottom: 4 }}>
        {(label && BAND_LABEL[label]) ?? label}
      </div>
      {RACE_FOCUS.map((g) => {
        const rate = row[g] as number | null;
        const n = (row[`${g}__n`] as number | undefined) ?? 0;
        return (
          <div key={g} style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
            <span style={{ color: palette[g] }}>{g}</span>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>
              {rate === null || rate === undefined
                ? `n=${n.toLocaleString()} (small-n, suppressed)`
                : `${(rate * 100).toFixed(1)}%  ·  n=${n.toLocaleString()}`}
            </span>
          </div>
        );
      })}
    </div>
  );
}
