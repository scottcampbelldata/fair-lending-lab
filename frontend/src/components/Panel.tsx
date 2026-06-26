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
        <header className="flex items-baseline justify-between border-b border-border px-5 py-3">
          <div>
            {title && (
              <h2 className="text-xs uppercase tracking-[0.14em] text-muted">{title}</h2>
            )}
            {subtitle && <p className="mt-0.5 text-sm text-text">{subtitle}</p>}
          </div>
          {right}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
