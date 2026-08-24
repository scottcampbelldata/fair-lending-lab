import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({
  API_BASE: "http://127.0.0.1:8702",
  api: {
    health: vi.fn(),
    overview: vi.fn(),
    hypotheses: vi.fn(),
    hypothesis: vi.fn(),
    familyCorrection: vi.fn(),
    denialByIncomeBand: vi.fn(),
    denialRatesByRace: vi.fn(),
  },
}));

import {
  api,
  type DenialByIncomeBand,
  type FamilyCorrection,
  type HypothesisSummary,
  type OverviewPayload,
} from "@/lib/api";
import { ThemeProvider } from "@/components/ThemeProvider";
import Page from "./page";

function pending<T>(): Promise<T> {
  return new Promise(() => {});
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function hypo(key: string): HypothesisSummary {
  return {
    key,
    title: key,
    h0: "H0",
    h1: "H1",
    direction: "two-sided",
    effect_of_interest: "rd",
    domain_question: "q",
    causal_caveat: "caveat",
    primary_method: null,
    p_value: null,
    effect_size: null,
    effect_label: null,
    n_a: null,
    n_b: null,
    ci_low: null,
    ci_high: null,
    refreshed_at: null,
  };
}

const FIVE_HYPOS: HypothesisSummary[] = [
  hypo("h1_denial_race"),
  hypo("h2_denial_ethnicity"),
  hypo("h3_rate_spread_priced"),
  hypo("h4_lender_effect"),
  hypo("h5_low_income_residual"),
];

const EMPTY_OVERVIEW: OverviewPayload = {
  counts: { loans: 0, hmda_raw: 0 },
  by_action: [],
  by_race: [],
  by_ethnicity: [],
  by_msa: [],
};

const EMPTY_FAMILY: FamilyCorrection = { family: [] };

const LIVE_HEALTH = {
  ok: true,
  version: "0.1.0",
  database: "flab",
  hmda_year: 2023,
  hmda_state: "MA",
};

function kpiValue(label: string): string | null | undefined {
  const node = screen.getByText(label);
  return node.parentElement?.querySelector("span.tabular-nums")?.textContent;
}

function renderPage() {
  return render(
    <ThemeProvider>
      <Page />
    </ThemeProvider>,
  );
}

beforeEach(() => {
  vi.mocked(api.health).mockImplementation(() => pending());
  vi.mocked(api.overview).mockImplementation(() => pending());
  vi.mocked(api.hypotheses).mockImplementation(() => pending());
  vi.mocked(api.hypothesis).mockImplementation(() => pending());
  vi.mocked(api.familyCorrection).mockImplementation(() => pending());
  vi.mocked(api.denialByIncomeBand).mockImplementation(() => pending());
  vi.mocked(api.denialRatesByRace).mockImplementation(() => pending());
});

describe("first-paint API status and KPI empty states", () => {
  it("shows connecting while health is pending and never the offline chip", () => {
    renderPage();
    expect(screen.getByText("connecting")).toBeInTheDocument();
    expect(screen.queryByText("api offline")).toBeNull();
    expect(screen.queryByText("api live")).toBeNull();
  });

  it("shows api live after health succeeds", async () => {
    vi.mocked(api.health).mockResolvedValue(LIVE_HEALTH);
    vi.mocked(api.overview).mockResolvedValue(EMPTY_OVERVIEW);
    vi.mocked(api.hypotheses).mockResolvedValue(FIVE_HYPOS);
    vi.mocked(api.familyCorrection).mockResolvedValue(EMPTY_FAMILY);
    vi.mocked(api.denialByIncomeBand).mockResolvedValue([]);
    vi.mocked(api.denialRatesByRace).mockResolvedValue([]);
    vi.mocked(api.hypothesis).mockResolvedValue({});

    renderPage();
    expect(await screen.findByText("api live")).toBeInTheDocument();
    expect(screen.queryByText("api offline")).toBeNull();
    expect(screen.queryByText("connecting")).toBeNull();
  });

  it("shows api offline and the api error banner when health rejects", async () => {
    vi.mocked(api.health).mockRejectedValue(new Error("network down"));

    renderPage();
    expect(await screen.findByText("api offline")).toBeInTheDocument();
    expect(screen.getByText(/api error/i)).toBeInTheDocument();
    expect(screen.queryByText("connecting")).toBeNull();
    expect(screen.queryByText("api live")).toBeNull();
  });

  it("shows an em dash on hypos-derived KPI tiles until five hypotheses resolve", async () => {
    const health = deferred<typeof LIVE_HEALTH>();
    const overview = deferred<OverviewPayload>();
    const hypos = deferred<HypothesisSummary[]>();
    const family = deferred<FamilyCorrection>();
    const bands = deferred<DenialByIncomeBand[]>();
    const race = deferred<
      { race_group: string; ethnicity_group: string; n: number; n_denied: number; denial_rate: number }[]
    >();

    vi.mocked(api.health).mockReturnValue(health.promise);
    vi.mocked(api.overview).mockReturnValue(overview.promise);
    vi.mocked(api.hypotheses).mockReturnValue(hypos.promise);
    vi.mocked(api.familyCorrection).mockReturnValue(family.promise);
    vi.mocked(api.denialByIncomeBand).mockReturnValue(bands.promise);
    vi.mocked(api.denialRatesByRace).mockReturnValue(race.promise);
    vi.mocked(api.hypothesis).mockResolvedValue({});

    renderPage();

    expect(kpiValue("hypotheses tested")).toBe("—");
    expect(kpiValue("significant at alpha 0.05")).toBe("—");
    expect(kpiValue("reject BH-FDR (q=0.05)")).toBe("—");
    expect(kpiValue("curated applications")).toBe("—");

    health.resolve(LIVE_HEALTH);
    overview.resolve(EMPTY_OVERVIEW);
    hypos.resolve(FIVE_HYPOS);
    family.resolve(EMPTY_FAMILY);
    bands.resolve([]);
    race.resolve([]);

    await waitFor(() => {
      expect(kpiValue("hypotheses tested")).toBe("5");
    });
    expect(kpiValue("significant at alpha 0.05")).toBe("0 / 5");
    expect(kpiValue("reject BH-FDR (q=0.05)")).toBe("0 / 5");
  });

  it("does not throw on Overview or Hypotheses tabs while hypos are pending", () => {
    renderPage();
    expect(screen.getByRole("button", { name: "Overview" })).toBeInTheDocument();
    expect(screen.queryByText("lead finding · H1")).toBeNull();
    expect(() => {
      fireEvent.click(screen.getByRole("button", { name: "Hypotheses" }));
    }).not.toThrow();
    expect(screen.getByRole("button", { name: "Hypotheses" })).toBeInTheDocument();
  });
});
