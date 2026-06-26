import type { ReactNode } from "react";

interface Props {
  label: string;
  value: string;
  unit?: string;
  sub?: ReactNode;
  spark?: number[];
}

export function KpiCard({ label, value, unit, sub, spark }: Props) {
  return (
    <div className="rounded-md border border-border bg-surface px-5 py-4">
      <div className="text-xs uppercase tracking-[0.12em] text-muted">{label}</div>
      <div className="mt-3 flex items-baseline">
        <span className="font-mono text-[2rem] font-medium leading-none tracking-[-0.02em] tabular-nums text-text">
          {value}
        </span>
        {unit && <span className="ml-1.5 text-sm font-normal text-muted">{unit}</span>}
      </div>
      <div className="mt-2 h-5 text-xs text-muted">{sub}</div>
      {spark && spark.length > 1 && <Sparkline values={spark} />}
    </div>
  );
}

function Sparkline({ values }: { values: number[] }) {
  const w = 140;
  const h = 24;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="mt-2 block">
      <polyline fill="none" stroke="#4f8bf5" strokeWidth={1.5} points={pts} />
    </svg>
  );
}
