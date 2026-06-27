// Number / p-value / effect-size formatting helpers.

// UI p-value display. Very small p-values are collapsed to "< 0.001": with
// n in the tens of thousands the exact value (e.g. 1e-102) is technically
// correct but reads as noise to a non-statistician. The exact float stays in
// the API payload and the exported results.json for anyone who wants it.
export function fmtP(p: number | null | undefined): string {
  if (p === null || p === undefined) return "-";
  if (p < 0.001) return "< 0.001";
  if (p < 0.01) return p.toFixed(4);
  return p.toFixed(3);
}

export function fmtEffect(v: number | null | undefined, digits = 3): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "-";
  return v.toFixed(digits);
}

export function fmtPct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "-";
  return `${(v * 100).toFixed(digits)}%`;
}

export function fmtN(v: number | null | undefined): string {
  if (v === null || v === undefined) return "-";
  return v.toLocaleString("en-US");
}

export function fmtCI(lo?: number | null, hi?: number | null, digits = 3): string {
  if (lo === null || lo === undefined || hi === null || hi === undefined) return "-";
  return `[${lo.toFixed(digits)}, ${hi.toFixed(digits)}]`;
}

export function isRejected(p: number | null | undefined, alpha = 0.05): boolean | null {
  if (p === null || p === undefined) return null;
  return p < alpha;
}
