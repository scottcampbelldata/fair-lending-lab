interface Props {
  hmdaYear?: number;
  hmdaState?: string;
  ok?: boolean;
}

export function AppHeader({ hmdaYear, hmdaState, ok }: Props) {
  return (
    <header className="border-b border-border bg-bg/60 backdrop-blur">
      <div className="mx-auto flex max-w-shell flex-col gap-2 px-6 py-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-sans text-2xl font-semibold tracking-tight text-text">
            Fair Lending Lab
          </h1>
          <p className="mt-1 text-sm text-muted">
            Hypothesis testing and statistical inference on CFPB HMDA mortgage applications.
            {hmdaState && hmdaYear ? (
              <span className="ml-1">{hmdaState} {hmdaYear} LAR.</span>
            ) : null}
          </p>
        </div>
        <div className="flex items-center gap-3 font-mono text-xs text-muted">
          <span className="flex items-center gap-2">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                ok ? "bg-accent" : "bg-bad"
              }`}
              style={ok ? { boxShadow: "0 0 0 3px rgba(79,139,245,0.18)" } : undefined}
            />
            {ok ? "api live" : "api offline"}
          </span>
          <span>v0.1.0</span>
        </div>
      </div>
    </header>
  );
}
