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
        <CartesianGrid stroke="#22262d" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="race_group"
          stroke="#8b8f99"
          tick={{ fill: "#8b8f99", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#272b33" }}
        />
        <YAxis
          stroke="#8b8f99"
          tick={{ fill: "#8b8f99", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#272b33" }}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
          domain={[0, "auto"]}
        />
        <Tooltip
          cursor={{ fill: "rgba(224,162,74,0.07)" }}
          contentStyle={{
            background: "#15171c",
            border: "1px solid #272b33",
            borderRadius: 6,
            color: "#e9e7e2",
            fontSize: 12,
          }}
          labelStyle={{ color: "#8b8f99" }}
          formatter={(value: number, _name, item) => {
            if (item?.dataKey === "denial_rate") {
              return [`${(value * 100).toFixed(2)}%`, "denial rate"];
            }
            return [value.toLocaleString(), String(_name)];
          }}
        />
        <Bar dataKey="denial_rate" fill="#6f93c0" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
