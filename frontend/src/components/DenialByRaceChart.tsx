"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTheme } from "./ThemeProvider";
import { chartTokens, RACE_SINGLE } from "@/lib/chartTheme";

interface Row {
  race_group: string;
  ethnicity_group?: string;
  n: number;
  n_denied: number;
  denial_rate: number;
}

export function DenialByRaceChart({ data }: { data: Row[] }) {
  const t = chartTokens(useTheme().theme);
  const ROW_ORDER = ["White", "Black", "Asian", "Hispanic", "Joint", "Native", "Pacific", "Multi", "Not Available"];
  const sorted = [...data].sort(
    (a, b) => ROW_ORDER.indexOf(a.race_group) - ROW_ORDER.indexOf(b.race_group),
  );
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sorted} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid stroke={t.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="race_group"
          stroke={t.tick}
          tick={{ fill: t.tick, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: t.axisLine }}
        />
        <YAxis
          stroke={t.tick}
          tick={{ fill: t.tick, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: t.axisLine }}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
          domain={[0, "auto"]}
        />
        <Tooltip
          cursor={{ fill: t.cursor }}
          contentStyle={{
            background: t.tooltipBg,
            border: `1px solid ${t.tooltipBorder}`,
            borderRadius: 6,
            color: t.tooltipText,
            fontSize: 12,
          }}
          labelStyle={{ color: t.tooltipLabel }}
          formatter={(value: number, _name, item) => {
            if (item?.dataKey === "denial_rate") {
              return [`${(value * 100).toFixed(2)}%`, "denial rate"];
            }
            return [value.toLocaleString(), String(_name)];
          }}
        />
        <Bar dataKey="denial_rate" fill={RACE_SINGLE} radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
