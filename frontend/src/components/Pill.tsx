interface Props {
  tone?: "neutral" | "sig" | "notsig" | "warn" | "accent";
  mono?: boolean;
  children: React.ReactNode;
}

export function Pill({ tone = "neutral", mono = true, children }: Props) {
  // Significance is "flagged", not "good": a rejected null here means a measured
  // disparity, so it reads as the amber signal. Fail-to-reject is a quiet
  // neutral, never red — a null result is not an error.
  const map: Record<string, string> = {
    neutral: "border-border bg-surface text-muted",
    sig: "border-accent-soft bg-accent-dim text-accent",
    notsig: "border-border bg-surface text-muted",
    warn: "border-[rgba(110,147,166,0.4)] bg-note-dim text-note",
    accent: "border-accent-soft bg-accent-dim text-accent",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs ${
        mono ? "font-mono" : "font-sans"
      } ${map[tone]}`}
    >
      {children}
    </span>
  );
}
