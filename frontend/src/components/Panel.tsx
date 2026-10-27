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
    <section className={`rounded-sm border border-border bg-surface ${className}`}>
      {(title || right) && (
        <header className="flex items-baseline justify-between gap-3 border-b border-border px-5 py-3.5">
          <div>
            {title && (
              <h2 className="text-sm italic text-muted first-letter:uppercase">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="mt-0.5 font-display text-xl font-normal leading-snug text-text">
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
