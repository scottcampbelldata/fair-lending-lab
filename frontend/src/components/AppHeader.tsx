import { ThemeToggle } from "./ThemeToggle";

interface Props {
  hmdaYear?: number;
  hmdaState?: string;
  status: "loading" | "live" | "offline";
}

export function AppHeader({ hmdaYear, hmdaState, status }: Props) {
  const live = status === "live";
  const offline = status === "offline";
  const label = live ? "api live" : offline ? "api offline" : "connecting";
  return (
    <div className="border-b border-border">
      <div className="mx-auto flex max-w-shell flex-wrap items-center justify-between gap-x-4 gap-y-2 px-6 py-3">
        <p className="text-sm text-muted">
          Fair Lending Lab, disparity screening on CFPB HMDA mortgage applications.
          {hmdaState && hmdaYear ? (
            <span className="ml-1 font-mono text-text">{hmdaState} {hmdaYear} LAR</span>
          ) : null}
        </p>
        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="inline-flex items-center gap-2 text-muted">
            <span
              className={`inline-block h-1.5 w-1.5 rounded-full ${
                live ? "bg-accent" : offline ? "bg-bad" : "bg-faint"
              }`}
            />
            {label}
          </span>
          <span className="text-muted">v0.1.0</span>
          <ThemeToggle />
        </div>
      </div>
    </div>
  );
}
