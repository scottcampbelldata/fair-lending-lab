// A blank bar that holds a value's place while it loads. It has no text, so
// nothing reads as a value (or a dash) before the data arrives.
export function Skeleton({ width, height = "0.8em" }: { width: string; height?: string }) {
  return (
    <span
      aria-hidden
      data-skeleton
      className="inline-block rounded-sm bg-border align-middle animate-pulse"
      style={{ width, height }}
    />
  );
}
