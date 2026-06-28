import type { HypothesisSummary } from "@/lib/api";
import { fmtCI, fmtEffect, fmtP } from "@/lib/format";

// The signature figure: a forest plot of every preregistered effect estimate
// against its null. Each row anchors the null at a fixed left position and
// scales its own positive extent, so the eye reads one thing across all rows —
// does the 95% interval clear zero? Units differ between hypotheses (risk
// difference, Hedges' g, eta squared), so each row is self-scaled and labelled
// with its metric; the numbers carry the exact magnitude.

const NULL_X = 16; // percent from left where the null (0) sits on every track.
const SPAN = 80; // percent of track width the positive extent maps across.

function pct(x: number, maxExtent: number): number {
  if (maxExtent <= 0) return NULL_X;
  const p = NULL_X + (x / maxExtent) * SPAN;
  return Math.max(2, Math.min(99, p));
}

function Row({ h }: { h: HypothesisSummary }) {
  const est = h.effect_size;
  const lo = h.ci_low;
  const hi = h.ci_high;
  const hasCI = lo !== null && lo !== undefined && hi !== null && hi !== undefined;
  const hasEst = est !== null && est !== undefined;

  // Flagged when the interval excludes the null, or (no CI) when p < 0.05.
  const clearsNull = hasCI
    ? lo! > 0 || hi! < 0
    : h.p_value !== null && h.p_value < 0.05;
  const tone = clearsNull ? "accent" : "muted";

  const maxExtent = Math.max(hi ?? est ?? 0, est ?? 0) * 1.18 || 1;
  const xEst = hasEst ? pct(est!, maxExtent) : NULL_X;
  const xLo = hasCI ? pct(lo!, maxExtent) : xEst;
  const xHi = hasCI ? pct(hi!, maxExtent) : xEst;

  return (
    <div className="grid grid-cols-1 items-center gap-x-5 gap-y-2 py-4 sm:grid-cols-[minmax(0,1.1fr)_minmax(0,1.5fr)_auto]">
      <div className="min-w-0">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-xs uppercase tracking-wider text-accent">
            {h.key.split("_")[0]}
          </span>
          <span className="truncate font-sans text-sm text-text">{h.title}</span>
        </div>
        <div className="mt-0.5 font-mono text-[11px] text-faint">
          {h.effect_label ?? "effect"} · {h.primary_method ?? "—"}
        </div>
      </div>

      {/* The ruler track. */}
      <div className="relative h-9">
        {/* baseline */}
        <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-border" />
        {/* null marker */}
        <div
          className="absolute top-1/2 h-5 w-px -translate-y-1/2 bg-border-strong"
          style={{ left: `${NULL_X}%` }}
          aria-hidden
        />
        <div
          className="absolute -bottom-0.5 -translate-x-1/2 font-mono text-[9px] text-faint"
          style={{ left: `${NULL_X}%` }}
          aria-hidden
        >
          0
        </div>
        {/* confidence interval whisker */}
        {hasCI && (
          <div
            className={`absolute top-1/2 h-[3px] origin-left -translate-y-1/2 rounded-full animate-draw-in ${
              tone === "accent" ? "bg-accent-soft" : "bg-border-strong"
            }`}
            style={{ left: `${xLo}%`, width: `${Math.max(xHi - xLo, 0.5)}%` }}
          />
        )}
        {/* point estimate */}
        {hasEst && (
          <div
            className={`absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-bg ${
              tone === "accent" ? "bg-accent" : "bg-muted"
            }`}
            style={{ left: `${xEst}%` }}
          />
        )}
      </div>

      <div className="text-left font-mono text-xs tabular-nums sm:text-right">
        <span className={tone === "accent" ? "text-text" : "text-muted"}>
          {fmtEffect(est)}
        </span>
        <span className="ml-2 text-faint">{hasCI ? fmtCI(lo, hi) : "no CI"}</span>
        <span className={`ml-2 ${clearsNull ? "text-accent" : "text-faint"}`}>
          p {fmtP(h.p_value)}
        </span>
      </div>
    </div>
  );
}

export function DisparityRuler({ hypos }: { hypos: HypothesisSummary[] }) {
  if (!hypos.length) return null;
  return (
    <div className="divide-y divide-border/60">
      {hypos.map((h) => (
        <Row key={h.key} h={h} />
      ))}
    </div>
  );
}
