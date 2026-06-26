interface Props {
  tone?: "neutral" | "sig" | "notsig" | "warn" | "accent";
  mono?: boolean;
  children: React.ReactNode;
}

export function Pill({ tone = "neutral", mono = true, children }: Props) {
  const map: Record<string, string> = {
    neutral: "border-border bg-surface text-muted",
    sig: "border-[rgba(63,185,80,0.4)] bg-[rgba(63,185,80,0.12)] text-good",
    notsig: "border-[rgba(248,81,73,0.4)] bg-[rgba(248,81,73,0.12)] text-bad",
    warn: "border-[rgba(210,153,34,0.4)] bg-[rgba(210,153,34,0.12)] text-warn",
    accent: "border-[rgba(79,139,245,0.4)] bg-accent-dim text-accent",
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
