"use client";

import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Props {
  mean: number;
  lo: number;
  hi: number;
  probAGtB: number;
}

// Renders an approximate Normal-shaped posterior density given mean and 95% CI.
// Used as a quick visual companion to the dashboard's Bayesian sensitivity block.
export function PosteriorChart({ mean, lo, hi, probAGtB }: Props) {
  const sd = (hi - lo) / (2 * 1.96);
  const xs = Array.from({ length: 121 }, (_, i) => mean + (i - 60) * (sd / 12));
  const ys = xs.map((x) => {
    const z = (x - mean) / sd;
    return Math.exp(-0.5 * z * z) / (sd * Math.sqrt(2 * Math.PI));
  });
  const rows = xs.map((x, i) => ({ x, y: ys[i] }));
  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <defs>
            <linearGradient id="posterior" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4f8bf5" stopOpacity={0.55} />
              <stop offset="100%" stopColor="#4f8bf5" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1f2733" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="x"
            stroke="#8b919e"
            tick={{ fill: "#8b919e", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "#23262d" }}
            tickFormatter={(v: number) => v.toFixed(2)}
          />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              background: "#131519",
              border: "1px solid #23262d",
              borderRadius: 6,
              color: "#e5e7eb",
              fontSize: 11,
            }}
            labelStyle={{ color: "#8b919e" }}
            formatter={(_v: number) => ["density", ""]}
            labelFormatter={(label: number) => `Delta = ${label.toFixed(3)}`}
          />
          <ReferenceLine x={0} stroke="#8b919e" strokeDasharray="3 3" />
          <ReferenceLine x={lo} stroke="#4f8bf5" strokeDasharray="2 4" />
          <ReferenceLine x={hi} stroke="#4f8bf5" strokeDasharray="2 4" />
          <Area dataKey="y" stroke="#4f8bf5" strokeWidth={1.5} fill="url(#posterior)" />
        </AreaChart>
      </ResponsiveContainer>
      <p className="mt-2 text-xs text-muted">
        P(group A &gt; group B) approx {probAGtB.toFixed(3)}. 95% credible interval drawn as
        dashed accent lines, zero as the dashed grey line.
      </p>
    </div>
  );
}
