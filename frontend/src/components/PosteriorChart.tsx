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
              <stop offset="0%" stopColor="#e0a24a" stopOpacity={0.5} />
              <stop offset="100%" stopColor="#e0a24a" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#22262d" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="x"
            stroke="#8b8f99"
            tick={{ fill: "#8b8f99", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "#272b33" }}
            tickFormatter={(v: number) => v.toFixed(2)}
          />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              background: "#15171c",
              border: "1px solid #272b33",
              borderRadius: 6,
              color: "#e9e7e2",
              fontSize: 11,
            }}
            labelStyle={{ color: "#8b8f99" }}
            formatter={(_v: number) => ["density", ""]}
            labelFormatter={(label: number) => `Delta = ${label.toFixed(3)}`}
          />
          <ReferenceLine x={0} stroke="#8b8f99" strokeDasharray="3 3" />
          <ReferenceLine x={lo} stroke="#e0a24a" strokeDasharray="2 4" />
          <ReferenceLine x={hi} stroke="#e0a24a" strokeDasharray="2 4" />
          <Area dataKey="y" stroke="#e0a24a" strokeWidth={1.5} fill="url(#posterior)" />
        </AreaChart>
      </ResponsiveContainer>
      <p className="mt-2 text-xs text-muted">
        P(group A &gt; group B) approx {probAGtB.toFixed(3)}. 95% credible interval drawn as
        dashed accent lines, zero as the dashed grey line.
      </p>
    </div>
  );
}
