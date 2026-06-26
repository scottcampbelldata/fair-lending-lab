// Thin API client. Reads NEXT_PUBLIC_API_BASE at build time. Defaults to local dev.

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8702";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} returned ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export interface HypothesisSummary {
  key: string;
  title: string;
  h0: string;
  h1: string;
  direction: string;
  effect_of_interest: string;
  domain_question: string;
  causal_caveat: string;
  primary_method: string | null;
  p_value: number | null;
  effect_size: number | null;
  effect_label: string | null;
  n_a: number | null;
  n_b: number | null;
  ci_low: number | null;
  ci_high: number | null;
  refreshed_at: string | null;
}

export interface OverviewPayload {
  counts: Record<string, number>;
  by_action: { action_taken: number; n: number }[];
  by_race: { race_group: string; n: number; n_denied: number; denial_rate: number }[];
  by_ethnicity: { ethnicity_group: string; n: number; n_denied: number; denial_rate: number }[];
  by_msa: { msa_md: string; n: number; n_denied: number; denial_rate: number }[];
}

export interface FamilyCorrection {
  family: {
    hypothesis_key: string;
    p_value: number;
    p_fdr: number;
    reject_fdr: boolean;
    p_bonferroni: number;
    reject_bonferroni: boolean;
  }[];
  fdr?: { method: string; m: number; q: number; cutoff_pvalue: number };
  bonferroni?: { method: string; m: number; alpha: number; threshold: number };
}

export interface DenialByIncomeBand {
  income_band: string;
  race_group: string;
  n: number;
  n_denied: number;
  denial_rate: number;
}

export const api = {
  health: () => get<{ ok: boolean; version: string; database: string; hmda_year: number; hmda_state: string }>("/health"),
  overview: () => get<OverviewPayload>("/api/overview"),
  hypotheses: () => get<HypothesisSummary[]>("/api/hypotheses"),
  hypothesis: (key: string) => get<Record<string, unknown>>(`/api/hypothesis/${key}`),
  familyCorrection: () => get<FamilyCorrection>("/api/family_correction"),
  denialByIncomeBand: () => get<DenialByIncomeBand[]>("/api/denial_by_income_band"),
  denialRatesByRace: () =>
    get<{ race_group: string; ethnicity_group: string; n: number; n_denied: number; denial_rate: number }[]>(
      "/api/denial_rates_by_race",
    ),
};
