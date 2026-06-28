import type { ReactNode } from "react";

interface Props {
  title?: string;
  subtitle?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, subtitle, right, children, className = "" }: Props) {
  return (
    <section className={`rounded-md border border-border bg-surface ${className}`}>
      {(title || right) && (
        <header className="flex items-baseline justify-between gap-3 border-b border-border px-5 py-3.5">
          <div>
            {title && (
              <h2 className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="mt-1 font-display text-base font-medium tracking-tight text-text">
                {subtitle}
              </p>
            )}
          </div>
          {right}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
