"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Row {
  income_band: string;
  race_group: string;
  n: number;
  n_denied: number;
  denial_rate: number;
}

const BAND_ORDER = ["under_50k", "50k_to_100k", "100k_to_150k", "150k_to_250k", "over_250k", "unknown"];
const RACE_FOCUS = ["White", "Black", "Hispanic", "Asian"];

// Minimum cell size before a denial rate is plotted. A band x race cell with a
// handful of applications can read 0% or 100% purely from sampling noise; an
// unsuppressed 100% bar looks broken even when it is technically correct.
// Below this n we drop the bar and label the cell small-n in the tooltip.
const MIN_N = 30;

const palette: Record<string, string> = {
  White: "#4f8bf5",
  Black: "#d29922",
  Hispanic: "#3fb950",
  Asian: "#a371f7",
};

type ChartRow = { income_band: string } & Record<string, number | string | null>;

export function DenialByIncomeChart({ data }: { data: Row[] }) {
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
        <CartesianGrid stroke="#1f2733" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="income_band"
          stroke="#8b919e"
          tick={{ fill: "#8b919e", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#23262d" }}
        />
        <YAxis
          stroke="#8b919e"
          tick={{ fill: "#8b919e", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#23262d" }}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
        />
        <Tooltip cursor={{ fill: "rgba(79,139,245,0.07)" }} content={<IncomeTooltip />} />
        <Legend wrapperStyle={{ color: "#8b919e", fontSize: 11 }} />
        {RACE_FOCUS.map((g) => (
          <Bar key={g} dataKey={g} fill={palette[g]} radius={[2, 2, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function IncomeTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ payload: ChartRow }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div
      style={{
        background: "#131519",
        border: "1px solid #23262d",
        borderRadius: 6,
        color: "#e5e7eb",
        fontSize: 12,
        padding: "8px 10px",
      }}
    >
      <div style={{ color: "#8b919e", marginBottom: 4 }}>{label}</div>
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
