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

export function DenialByIncomeChart({ data }: { data: Row[] }) {
  const pivot: Record<string, Record<string, number>> = {};
  for (const r of data) {
    if (!RACE_FOCUS.includes(r.race_group)) continue;
    pivot[r.income_band] ??= { income_band: 0 as unknown as number };
    pivot[r.income_band][r.race_group] = r.denial_rate;
  }
  const rows = BAND_ORDER.filter((b) => pivot[b]).map((b) => ({
    income_band: b,
    ...pivot[b],
  }));
  const palette: Record<string, string> = {
    White: "#4f8bf5",
    Black: "#d29922",
    Hispanic: "#3fb950",
    Asian: "#a371f7",
  };

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
        <Tooltip
          cursor={{ fill: "rgba(79,139,245,0.07)" }}
          contentStyle={{
            background: "#131519",
            border: "1px solid #23262d",
            borderRadius: 6,
            color: "#e5e7eb",
            fontSize: 12,
          }}
          labelStyle={{ color: "#8b919e" }}
          formatter={(value: number, name) => [`${(value * 100).toFixed(2)}%`, String(name)]}
        />
        <Legend wrapperStyle={{ color: "#8b919e", fontSize: 11 }} />
        {RACE_FOCUS.map((g) => (
          <Bar key={g} dataKey={g} fill={palette[g]} radius={[2, 2, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
