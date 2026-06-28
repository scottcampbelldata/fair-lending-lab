import type { ReactNode } from "react";

interface Props {
  label: string;
  value: string;
  unit?: string;
  sub?: ReactNode;
  /** Optional emphasis: render the value in the signal colour. */
  flagged?: boolean;
}

export function KpiCard({ label, value, unit, sub, flagged }: Props) {
  return (
    <div className="group rounded-md border border-border bg-surface px-5 py-4 transition-colors hover:border-border-strong">
      <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">
        {label}
      </div>
      <div className="mt-3 flex items-baseline">
        <span
          className={`font-mono text-[2rem] font-medium leading-none tracking-[-0.02em] tabular-nums ${
            flagged ? "text-accent" : "text-text"
          }`}
        >
          {value}
        </span>
        {unit && <span className="ml-1.5 text-sm font-normal text-muted">{unit}</span>}
      </div>
      <div className="mt-2.5 text-xs leading-snug text-muted">{sub}</div>
    </div>
  );
}
