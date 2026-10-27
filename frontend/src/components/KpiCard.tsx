import type { ReactNode } from "react";
import { Skeleton } from "./Skeleton";

interface Props {
  label: string;
  /** An empty string shows a blank placeholder while the value loads. */
  value: string;
  unit?: string;
  sub?: ReactNode;
  /** Optional emphasis: render the value in the signal colour. */
  flagged?: boolean;
}

export function KpiCard({ label, value, unit, sub, flagged }: Props) {
  return (
    <div className="group rounded-sm border border-border bg-surface px-5 py-4 transition-colors hover:border-border-strong">
      <div className="text-sm text-muted first-letter:uppercase">
        {label}
      </div>
      <div className="mt-3 flex items-baseline">
        <span
          className={`font-mono text-[2rem] font-normal leading-none tabular-nums ${
            flagged ? "text-accent" : "text-text"
          }`}
        >
          {value === "" ? <Skeleton width="2.5ch" /> : value}
        </span>
        {unit && <span className="ml-1.5 text-sm font-normal text-muted">{unit}</span>}
      </div>
      <div className="mt-2.5 text-sm leading-snug text-muted">{sub}</div>
    </div>
  );
}
