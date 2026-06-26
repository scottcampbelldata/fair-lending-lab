import { fmtCI, fmtEffect, fmtN, fmtP } from "@/lib/format";
import type { HypothesisSummary } from "@/lib/api";
import { Pill } from "./Pill";

interface Props {
  h: HypothesisSummary;
  active?: boolean;
  onClick?: () => void;
}

export function HypothesisCard({ h, active, onClick }: Props) {
  const sig = h.p_value !== null && h.p_value < 0.05;
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group w-full rounded-md border bg-surface p-5 text-left transition-colors ${
        active ? "border-accent" : "border-border hover:border-muted"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs text-muted">{h.key}</span>
        {h.p_value !== null && (
          <Pill tone={sig ? "sig" : "notsig"}>
            {sig ? "reject H0" : "fail to reject"}
          </Pill>
        )}
        <Pill>{h.primary_method ?? "no result"}</Pill>
      </div>
      <h3 className="mt-2 text-base font-semibold text-text">{h.title}</h3>
      <p className="mt-1 text-sm leading-relaxed text-muted">
        <span className="font-mono text-text">H0:</span> {h.h0}
        {"  "}
        <span className="font-mono text-text">H1:</span> {h.h1}
      </p>
      <div className="mt-3 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
        <Stat label="p value" value={fmtP(h.p_value)} mono />
        <Stat
          label={h.effect_label ?? "effect"}
          value={fmtEffect(h.effect_size)}
          mono
        />
        <Stat label="95% CI" value={fmtCI(h.ci_low, h.ci_high)} mono />
        <Stat
          label="sample size"
          value={`${fmtN(h.n_a)} / ${fmtN(h.n_b)}`}
          mono
        />
      </div>
    </button>
  );
}

function Stat({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-muted">{label}</div>
      <div className={`mt-0.5 text-sm text-text ${mono ? "font-mono tabular-nums" : ""}`}>
        {value}
      </div>
    </div>
  );
}
