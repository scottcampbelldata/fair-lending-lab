import { ThemeToggle } from "./ThemeToggle";

interface Props {
  hmdaYear?: number;
  hmdaState?: string;
  ok?: boolean;
}

export function AppHeader({ hmdaYear, hmdaState, ok }: Props) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-bg/80 backdrop-blur">
      <div className="mx-auto flex max-w-shell flex-col gap-3 px-6 py-5 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex items-center gap-3.5">
          <LabMark />
          <div>
            <h1 className="font-display text-xl font-semibold tracking-tight text-text">
              Fair Lending Lab
            </h1>
            <p className="mt-0.5 text-sm text-muted">
              Disparity screening on CFPB HMDA mortgage applications.
              {hmdaState && hmdaYear ? (
                <span className="ml-1 font-mono text-text">{hmdaState} {hmdaYear} LAR</span>
              ) : null}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2.5 font-mono text-xs">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-2.5 py-1 text-muted">
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${ok ? "bg-accent" : "bg-bad"}`}
              style={ok ? { boxShadow: "0 0 0 3px rgba(224,162,74,0.18)" } : undefined}
            />
            {ok ? "api live" : "api offline"}
          </span>
          <span className="text-faint">v0.1.0</span>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

// A small instrument mark: a point estimate sitting to the right of the null —
// the page's whole argument compressed into a glyph.
function LabMark() {
  return (
    <svg
      width="34"
      height="34"
      viewBox="0 0 34 34"
      fill="none"
      aria-hidden
      className="shrink-0"
    >
      <rect
        x="0.5"
        y="0.5"
        width="33"
        height="33"
        rx="7"
        className="stroke-border"
      />
      <line x1="11" y1="9" x2="11" y2="25" strokeWidth="1.5" className="stroke-faint" />
      <line
        x1="11"
        y1="17"
        x2="26"
        y2="17"
        strokeWidth="1.5"
        className="stroke-border-strong"
      />
      <circle cx="22" cy="17" r="3.5" className="fill-accent" />
    </svg>
  );
}
