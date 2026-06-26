"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface Row {
  race_group: string;
  ethnicity_group?: string;
  n: number;
  n_denied: number;
  denial_rate: number;
}

export function DenialByRaceChart({ data }: { data: Row[] }) {
  const ROW_ORDER = ["White", "Black", "Asian", "Hispanic", "Joint", "Native", "Pacific", "Multi", "Not Available"];
  const sorted = [...data].sort(
    (a, b) => ROW_ORDER.indexOf(a.race_group) - ROW_ORDER.indexOf(b.race_group),
  );
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sorted} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid stroke="#1f2733" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="race_group"
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
          domain={[0, "auto"]}
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
          formatter={(value: number, _name, item) => {
            if (item?.dataKey === "denial_rate") {
              return [`${(value * 100).toFixed(2)}%`, "denial rate"];
            }
            return [value.toLocaleString(), String(_name)];
          }}
        />
        <Bar dataKey="denial_rate" fill="#4f8bf5" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
