"use client";

import { useEffect, useMemo, useState } from "react";
import {
  api,
  API_BASE,
  type DenialByIncomeBand,
  type FamilyCorrection,
  type HypothesisSummary,
  type OverviewPayload,
} from "@/lib/api";
import { fmtCI, fmtEffect, fmtN, fmtP, fmtPct } from "@/lib/format";
import { AppHeader } from "@/components/AppHeader";
import { DenialByIncomeChart } from "@/components/DenialByIncomeChart";
import { DenialByRaceChart } from "@/components/DenialByRaceChart";
import { HypothesisCard } from "@/components/HypothesisCard";
import { KpiCard } from "@/components/KpiCard";
import { Panel } from "@/components/Panel";
import { Pill } from "@/components/Pill";
import { PosteriorChart } from "@/components/PosteriorChart";

type Health = { ok: boolean; version: string; database: string; hmda_year: number; hmda_state: string };
type HypothesisDetail = Record<string, unknown> & {
  primary?: Record<string, unknown>;
  secondary?: Record<string, unknown>;
  groups?: Record<string, unknown>;
  assumptions?: Record<string, unknown>;
  power?: Record<string, unknown>;
  causal_caveat?: string;
};

export default function Page() {
  const [health, setHealth] = useState<Health | null>(null);
  const [overview, setOverview] = useState<OverviewPayload | null>(null);
  const [hypos, setHypos] = useState<HypothesisSummary[]>([]);
  const [family, setFamily] = useState<FamilyCorrection | null>(null);
  const [byBand, setByBand] = useState<DenialByIncomeBand[]>([]);
  const [byRace, setByRace] = useState<
    { race_group: string; n: number; n_denied: number; denial_rate: number }[]
  >([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [detail, setDetail] = useState<HypothesisDetail | null>(null);
  const [tab, setTab] = useState<"overview" | "hypotheses" | "family" | "methods" | "about">(
    "overview",
  );
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [h, ov, hs, fc, bb, brc] = await Promise.all([
          api.health(),
          api.overview(),
          api.hypotheses(),
          api.familyCorrection(),
          api.denialByIncomeBand(),
          api.denialRatesByRace(),
        ]);
        setHealth(h);
        setOverview(ov);
        setHypos(hs);
        setFamily(fc);
        setByBand(bb);
        setByRace(brc.filter((r) => r.race_group !== "Joint" && r.ethnicity_group !== "Joint"));
        if (hs.length) setSelectedKey(hs[0].key);
      } catch (e) {
        setErr(String(e));
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedKey) return;
    api
      .hypothesis(selectedKey)
      .then((d) => setDetail(d as HypothesisDetail))
      .catch((e) => setErr(String(e)));
  }, [selectedKey]);

  const sigCount = hypos.filter((h) => h.p_value !== null && h.p_value < 0.05).length;
  const fdrReject = family?.family.filter((f) => f.reject_fdr).length ?? 0;
  const bonfReject = family?.family.filter((f) => f.reject_bonferroni).length ?? 0;
  const headline = hypos.find((h) => h.key === "h1_denial_race");
  const headlineDetail = useMemo(() => detail, [detail]);

  return (
    <div className="min-h-screen">
      <AppHeader hmdaYear={health?.hmda_year} hmdaState={health?.hmda_state} ok={!!health?.ok} />
      <main className="mx-auto max-w-shell px-6 py-6">
        {err && (
          <div className="mb-4 rounded-md border border-bad/40 bg-[rgba(248,81,73,0.08)] p-3 text-sm text-bad">
            {err}
          </div>
        )}

        <CalloutWhatMattersNow headline={headline} />

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <KpiCard
            label="curated applications"
            value={fmtN(overview?.counts.loans ?? null)}
            sub={
              overview ? (
                <>filtered from {fmtN(overview.counts.hmda_raw)} raw LAR rows</>
              ) : (
                "loading"
              )
            }
            spark={[1, 1, 2, 3, 5, 8, 8, 10, 12, 14, 14, 16]}
          />
          <KpiCard
            label="hypotheses tested"
            value={`${hypos.length}`}
            sub="preregistered H0 / H1 with effect targets"
          />
          <KpiCard
            label="significant at alpha 0.05"
            value={`${sigCount} / ${hypos.length}`}
            sub="raw, uncorrected"
          />
          <KpiCard
            label="reject BH-FDR (q=0.05)"
            value={`${fdrReject} / ${hypos.length}`}
            sub={`Bonferroni at alpha/m: ${bonfReject} / ${hypos.length}`}
          />
        </div>

        <TabNav tab={tab} onChange={setTab} />

        {tab === "overview" && (
          <OverviewTab
            overview={overview}
            byRace={byRace}
            byBand={byBand}
            hypos={hypos}
          />
        )}
        {tab === "hypotheses" && (
          <HypothesesTab
            hypos={hypos}
            selectedKey={selectedKey}
            onSelect={setSelectedKey}
            detail={headlineDetail}
          />
        )}
        {tab === "family" && family && <FamilyTab family={family} hypos={hypos} />}
        {tab === "methods" && <MethodsTab />}
        {tab === "about" && <AboutTab health={health} />}

        <footer className="mt-12 border-t border-border pt-4 text-xs text-muted">
          Fair Lending Lab. Database <span className="font-mono">{health?.database}</span>.
          Source: CFPB FFIEC HMDA LAR, {health?.hmda_state} {health?.hmda_year}. Public data,
          no PII. Screening signal only. See the causal caveat on each hypothesis.
        </footer>
      </main>
    </div>
  );
}

function CalloutWhatMattersNow({ headline }: { headline: HypothesisSummary | undefined }) {
  if (!headline) return null;
  const rd = headline.effect_size;
  const ci = `[${(headline.ci_low ?? 0).toFixed(3)}, ${(headline.ci_high ?? 0).toFixed(3)}]`;
  return (
    <section className="rounded-md border border-accent/40 bg-accent-dim px-5 py-4">
      <div className="text-xs uppercase tracking-wider text-accent">what matters now</div>
      <p className="mt-2 text-sm leading-relaxed text-text">
        <span className="font-mono text-accent">H1.</span>{" "}
        <strong>Black non-Hispanic applicants show a higher observed denial rate</strong> than
        White non-Hispanic applicants for first-lien conventional owner-occupied home-purchase
        loans, by{" "}
        <span className="font-mono text-text">
          risk difference = {fmtPct(rd, 1)} (95% CI {ci})
        </span>
        . Confirmed by a two-proportion z-test (p = {fmtP(headline.p_value)}) and by the
        Wald-CI odds ratio. The disparity persists inside the lowest income band (H5). All
        five primary tests reject at BH-FDR q = 0.05 and Bonferroni. <em>This is a
        screening signal, not a causal claim,</em> see the per-hypothesis caveat.
      </p>
    </section>
  );
}

function TabNav({
  tab,
  onChange,
}: {
  tab: string;
  onChange: (t: "overview" | "hypotheses" | "family" | "methods" | "about") => void;
}) {
  const tabs = [
    ["overview", "Overview"],
    ["hypotheses", "Hypotheses"],
    ["family", "Family correction"],
    ["methods", "Methods"],
    ["about", "About"],
  ] as const;
  return (
    <nav className="mt-6 flex flex-wrap gap-1 border-b border-border">
      {tabs.map(([k, label]) => (
        <button
          key={k}
          type="button"
          onClick={() => onChange(k)}
          className={`-mb-px border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === k
              ? "border-accent text-text"
              : "border-transparent text-muted hover:text-text"
          }`}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}

function OverviewTab({
  overview,
  byRace,
  byBand,
  hypos,
}: {
  overview: OverviewPayload | null;
  byRace: { race_group: string; n: number; n_denied: number; denial_rate: number }[];
  byBand: DenialByIncomeBand[];
  hypos: HypothesisSummary[];
}) {
  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-2">
      <Panel title="denial rate by race" subtitle="all applications">
        <DenialByRaceChart data={byRace} />
        <p className="mt-2 text-xs text-muted">
          Raw rates without covariate adjustment. See hypothesis cards for tests and CIs.
        </p>
      </Panel>
      <Panel title="denial rate by income band and race" subtitle="non-joint applicants">
        <DenialByIncomeChart data={byBand} />
        <p className="mt-2 text-xs text-muted">
          Income binning is the simplest control HMDA supports. The Black vs White spread
          persists across all bands (H5). Cells with n &lt; 30 are suppressed; small-n cells
          produce unstable rates. Hover any bar for the rate and exact n.
        </p>
      </Panel>
      <Panel title="result summary" subtitle="five preregistered hypotheses" className="lg:col-span-2">
        <div className="-mx-5 -my-5 overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead className="border-b border-border bg-bg/40">
              <tr className="text-left text-[10px] uppercase tracking-wider text-muted">
                <th className="px-4 py-2">key</th>
                <th className="px-4 py-2">title</th>
                <th className="px-4 py-2">method</th>
                <th className="px-4 py-2">p value</th>
                <th className="px-4 py-2">effect</th>
                <th className="px-4 py-2">95% CI</th>
                <th className="px-4 py-2">n A / B</th>
              </tr>
            </thead>
            <tbody>
              {hypos.map((h) => {
                const sig = h.p_value !== null && h.p_value < 0.05;
                return (
                  <tr key={h.key} className="border-b border-border/50">
                    <td className="px-4 py-2 font-mono text-xs text-muted">{h.key}</td>
                    <td className="px-4 py-2 text-text">{h.title}</td>
                    <td className="px-4 py-2 font-mono text-xs text-muted">
                      {h.primary_method ?? "-"}
                    </td>
                    <td className="px-4 py-2 font-mono tabular-nums">
                      <span className={sig ? "text-good" : "text-muted"}>
                        {fmtP(h.p_value)}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono tabular-nums">
                      {fmtEffect(h.effect_size)}{" "}
                      <span className="text-xs text-muted">{h.effect_label ?? ""}</span>
                    </td>
                    <td className="px-4 py-2 font-mono tabular-nums">
                      {fmtCI(h.ci_low, h.ci_high)}
                    </td>
                    <td className="px-4 py-2 font-mono tabular-nums text-muted">
                      {fmtN(h.n_a)} / {fmtN(h.n_b)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function HypothesesTab({
  hypos,
  selectedKey,
  onSelect,
  detail,
}: {
  hypos: HypothesisSummary[];
  selectedKey: string | null;
  onSelect: (k: string) => void;
  detail: HypothesisDetail | null;
}) {
  const selected = hypos.find((h) => h.key === selectedKey);
  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_1.4fr]">
      <div className="space-y-3">
        {hypos.map((h) => (
          <HypothesisCard
            key={h.key}
            h={h}
            active={h.key === selectedKey}
            onClick={() => onSelect(h.key)}
          />
        ))}
      </div>
      <div className="space-y-4">
        {selected && (
          <Panel
            title={selected.key}
            subtitle={selected.title}
            right={
              <Pill tone={selected.p_value !== null && selected.p_value < 0.05 ? "sig" : "notsig"}>
                {selected.p_value !== null && selected.p_value < 0.05
                  ? "reject H0"
                  : "fail to reject"}
              </Pill>
            }
          >
            <p className="text-sm text-text">{selected.domain_question}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-muted">
              <div>
                <div className="text-[10px] uppercase tracking-wider">direction</div>
                <div className="mt-0.5 text-text">{selected.direction}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider">effect of interest</div>
                <div className="mt-0.5 text-text">{selected.effect_of_interest}</div>
              </div>
            </div>
            <CausalCaveat caveat={selected.causal_caveat} />
          </Panel>
        )}
        {detail && <MethodPanel detail={detail} selected={selected} />}
      </div>
    </div>
  );
}

function CausalCaveat({ caveat }: { caveat: string }) {
  return (
    <div className="mt-4 rounded-md border border-warn/30 bg-[rgba(210,153,34,0.08)] p-3">
      <div className="text-[10px] uppercase tracking-wider text-warn">causal caveat</div>
      <p className="mt-1 text-sm leading-relaxed text-text">{caveat}</p>
    </div>
  );
}

function MethodPanel({
  detail,
  selected,
}: {
  detail: HypothesisDetail;
  selected: HypothesisSummary | undefined;
}) {
  const primary = (detail.primary ?? {}) as Record<string, unknown>;
  const secondary = (detail.secondary ?? {}) as Record<string, unknown>;
  const groups = (detail.groups ?? {}) as Record<string, Record<string, unknown>>;
  const bayes = secondary["bayesian"] as
    | { posterior_median_diff: number; credible_low: number; credible_high: number; prob_a_gt_b: number; bf10_bic: number; log_bf10_bic?: number }
    | undefined;
  const stratified = secondary["stratified_by_income_band"] as
    | Array<{ income_band: string; p_black: number; p_white: number; rd: number; rd_ci_low: number; rd_ci_high: number; n_black: number; n_white: number; reject_fdr?: boolean }>
    | undefined;
  const pairwise = secondary["pairwise_two_prop"] as
    | Array<{ pair: string; p_a: number; p_b: number; rd: number; rd_ci_low: number; rd_ci_high: number; p_value: number; reject_fdr?: boolean }>
    | undefined;
  const lenderTable = (detail as { lender_table?: Array<{ lender_label: string; lei: string; n: number; x_denied: number }> })
    .lender_table;

  return (
    <Panel title="method panel" subtitle="parametric, non-parametric, resampling">
      <table className="w-full text-sm">
        <thead className="text-left text-[10px] uppercase tracking-wider text-muted">
          <tr>
            <th className="py-1 pr-3">test</th>
            <th className="py-1 pr-3">p value</th>
            <th className="py-1 pr-3">statistic</th>
            <th className="py-1 pr-3">effect</th>
            <th className="py-1 pr-3">95% CI</th>
          </tr>
        </thead>
        <tbody className="text-text">
          <MethodRow row={primary} />
          {Object.entries(secondary).map(([name, body]) => {
            if (!body || typeof body !== "object") return null;
            if (name === "stratified_by_income_band" || name === "income_band_fdr") return null;
            if (name === "pairwise_two_prop" || name === "bh_fdr" || name === "bonferroni") return null;
            const b = body as Record<string, unknown>;
            return <MethodRow key={name} row={{ ...b, method: name }} />;
          })}
        </tbody>
      </table>

      {bayes && (
        <div className="mt-5 rounded-md border border-border bg-bg/40 p-4">
          <div className="text-xs uppercase tracking-wider text-muted">Bayesian sensitivity</div>
          <div className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="posterior median Δμ" value={bayes.posterior_median_diff.toFixed(3)} />
            <Stat
              label="95% credible interval"
              value={`[${bayes.credible_low.toFixed(2)}, ${bayes.credible_high.toFixed(2)}]`}
            />
            <Stat label="P(group A > group B)" value={bayes.prob_a_gt_b.toFixed(3)} />
            <Stat
              label="BF10 (BIC approx)"
              value={
                bayes.log_bf10_bic && bayes.log_bf10_bic > 700
                  ? `log = ${bayes.log_bf10_bic.toFixed(1)}`
                  : bayes.bf10_bic.toExponential(2)
              }
            />
          </div>
          <div className="mt-4">
            <PosteriorChart
              mean={bayes.posterior_median_diff}
              lo={bayes.credible_low}
              hi={bayes.credible_high}
              probAGtB={bayes.prob_a_gt_b}
            />
          </div>
        </div>
      )}

      {stratified && stratified.length > 0 && (
        <div className="mt-5">
          <div className="text-xs uppercase tracking-wider text-muted">
            stratified sensitivity by income band, BH-FDR adjusted
          </div>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-left text-muted">
                <tr>
                  <th className="py-1 pr-3">band</th>
                  <th className="py-1 pr-3">n black</th>
                  <th className="py-1 pr-3">p black</th>
                  <th className="py-1 pr-3">n white</th>
                  <th className="py-1 pr-3">p white</th>
                  <th className="py-1 pr-3">RD</th>
                  <th className="py-1 pr-3">RD CI</th>
                  <th className="py-1 pr-3">FDR</th>
                </tr>
              </thead>
              <tbody className="font-mono text-text">
                {stratified.map((r) => (
                  <tr key={r.income_band} className="border-t border-border/40">
                    <td className="py-1 pr-3 font-sans">{r.income_band}</td>
                    <td className="py-1 pr-3">{r.n_black.toLocaleString()}</td>
                    <td className="py-1 pr-3">{(r.p_black * 100).toFixed(1)}%</td>
                    <td className="py-1 pr-3">{r.n_white.toLocaleString()}</td>
                    <td className="py-1 pr-3">{(r.p_white * 100).toFixed(1)}%</td>
                    <td className="py-1 pr-3">{(r.rd * 100).toFixed(1)} pp</td>
                    <td className="py-1 pr-3">
                      [{(r.rd_ci_low * 100).toFixed(1)}, {(r.rd_ci_high * 100).toFixed(1)}]
                    </td>
                    <td className="py-1 pr-3">
                      {r.reject_fdr ? (
                        <Pill tone="sig">reject</Pill>
                      ) : (
                        <Pill tone="notsig">no</Pill>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {pairwise && pairwise.length > 0 && (
        <div className="mt-5">
          <div className="text-xs uppercase tracking-wider text-muted">
            pairwise two-proportion tests, BH-FDR adjusted
          </div>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-left text-muted">
                <tr>
                  <th className="py-1 pr-3">pair</th>
                  <th className="py-1 pr-3">p A</th>
                  <th className="py-1 pr-3">p B</th>
                  <th className="py-1 pr-3">RD</th>
                  <th className="py-1 pr-3">p</th>
                  <th className="py-1 pr-3">FDR</th>
                </tr>
              </thead>
              <tbody className="font-mono text-text">
                {pairwise.slice(0, 12).map((r) => (
                  <tr key={r.pair} className="border-t border-border/40">
                    <td className="py-1 pr-3 font-sans">{r.pair}</td>
                    <td className="py-1 pr-3">{(r.p_a * 100).toFixed(1)}%</td>
                    <td className="py-1 pr-3">{(r.p_b * 100).toFixed(1)}%</td>
                    <td className="py-1 pr-3">{(r.rd * 100).toFixed(1)} pp</td>
                    <td className="py-1 pr-3">{fmtP(r.p_value)}</td>
                    <td className="py-1 pr-3">
                      {r.reject_fdr ? (
                        <Pill tone="sig">reject</Pill>
                      ) : (
                        <Pill tone="notsig">no</Pill>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {lenderTable && (
        <div className="mt-5">
          <div className="text-xs uppercase tracking-wider text-muted">top 10 lenders</div>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-left text-muted">
                <tr>
                  <th className="py-1 pr-3">label</th>
                  <th className="py-1 pr-3">lei</th>
                  <th className="py-1 pr-3">n</th>
                  <th className="py-1 pr-3">denials</th>
                  <th className="py-1 pr-3">denial rate</th>
                </tr>
              </thead>
              <tbody className="font-mono text-text">
                {lenderTable.map((r) => (
                  <tr key={r.lei} className="border-t border-border/40">
                    <td className="py-1 pr-3 font-sans">{r.lender_label}</td>
                    <td className="py-1 pr-3 text-muted">{r.lei}</td>
                    <td className="py-1 pr-3">{r.n.toLocaleString()}</td>
                    <td className="py-1 pr-3">{r.x_denied.toLocaleString()}</td>
                    <td className="py-1 pr-3">{((r.x_denied / r.n) * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <details className="mt-5">
        <summary className="cursor-pointer text-xs uppercase tracking-wider text-muted">
          group summary
        </summary>
        <pre className="mt-2 overflow-x-auto rounded bg-bg/50 p-3 text-xs text-muted">
          {JSON.stringify(groups, null, 2)}
        </pre>
      </details>
    </Panel>
  );
}

function MethodRow({ row }: { row: Record<string, unknown> }) {
  const method = String(row.method ?? "");
  const p = row.p_value as number | null | undefined;
  const stat = (row.statistic ?? row.observed_diff) as number | null | undefined;
  const eff = (row.effect_size ?? row.estimate ?? row.eta_squared) as
    | number
    | null
    | undefined;
  const lo = row.ci_low as number | null | undefined;
  const hi = row.ci_high as number | null | undefined;
  return (
    <tr className="border-t border-border/40">
      <td className="py-1 pr-3 font-mono text-xs">{method}</td>
      <td className="py-1 pr-3 font-mono tabular-nums">{fmtP(p)}</td>
      <td className="py-1 pr-3 font-mono tabular-nums">{fmtEffect(stat, 3)}</td>
      <td className="py-1 pr-3 font-mono tabular-nums">
        {fmtEffect(eff, 3)}{" "}
        <span className="text-xs text-muted">{(row.effect_label as string) ?? ""}</span>
      </td>
      <td className="py-1 pr-3 font-mono tabular-nums">{fmtCI(lo, hi)}</td>
    </tr>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-0.5 font-mono text-sm tabular-nums text-text">{value}</div>
    </div>
  );
}

function FamilyTab({ family, hypos }: { family: FamilyCorrection; hypos: HypothesisSummary[] }) {
  const titles = Object.fromEntries(hypos.map((h) => [h.key, h.title]));
  return (
    <div className="mt-6 space-y-4">
      <Panel title="family-wise correction" subtitle="BH-FDR and Bonferroni across primary tests">
        <div className="-mx-5 -my-5 overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead className="border-b border-border">
              <tr className="text-left text-[10px] uppercase tracking-wider text-muted">
                <th className="px-4 py-2">key</th>
                <th className="px-4 py-2">title</th>
                <th className="px-4 py-2">p</th>
                <th className="px-4 py-2">BH-FDR adjusted</th>
                <th className="px-4 py-2">reject FDR</th>
                <th className="px-4 py-2">Bonferroni adjusted</th>
                <th className="px-4 py-2">reject Bonf</th>
              </tr>
            </thead>
            <tbody>
              {family.family.map((r) => (
                <tr key={r.hypothesis_key} className="border-b border-border/40">
                  <td className="px-4 py-2 font-mono text-xs text-muted">{r.hypothesis_key}</td>
                  <td className="px-4 py-2 text-text">{titles[r.hypothesis_key] ?? ""}</td>
                  <td className="px-4 py-2 font-mono tabular-nums">{fmtP(r.p_value)}</td>
                  <td className="px-4 py-2 font-mono tabular-nums">{fmtP(r.p_fdr)}</td>
                  <td className="px-4 py-2">
                    {r.reject_fdr ? <Pill tone="sig">reject</Pill> : <Pill tone="notsig">no</Pill>}
                  </td>
                  <td className="px-4 py-2 font-mono tabular-nums">{fmtP(r.p_bonferroni)}</td>
                  <td className="px-4 py-2">
                    {r.reject_bonferroni ? (
                      <Pill tone="sig">reject</Pill>
                    ) : (
                      <Pill tone="notsig">no</Pill>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <div className="grid gap-4 sm:grid-cols-2">
        <KpiCard
          label="BH-FDR cutoff p"
          value={family.fdr ? family.fdr.cutoff_pvalue.toExponential(2) : "-"}
          sub={family.fdr ? `q = ${family.fdr.q}, m = ${family.fdr.m}` : ""}
        />
        <KpiCard
          label="Bonferroni threshold"
          value={family.bonferroni ? family.bonferroni.threshold.toExponential(2) : "-"}
          sub={
            family.bonferroni
              ? `alpha / m = ${family.bonferroni.alpha} / ${family.bonferroni.m}`
              : ""
          }
        />
      </div>
    </div>
  );
}

function MethodsTab() {
  return (
    <div className="mt-6 space-y-4">
      <Panel title="method stack" subtitle="every hypothesis gets multiple lenses">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-muted">
            <tr>
              <th className="py-1 pr-3">layer</th>
              <th className="py-1 pr-3">methods</th>
            </tr>
          </thead>
          <tbody className="text-text">
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">parametric</td><td className="py-2 pr-3">Welch t test, one-way ANOVA with eta squared and omega squared</td></tr>
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">non-parametric</td><td className="py-2 pr-3">Mann-Whitney U with rank-biserial r, Kruskal-Wallis H with epsilon squared</td></tr>
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">distribution-free</td><td className="py-2 pr-3">Permutation test of mean difference, 5,000 shuffles</td></tr>
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">resampling</td><td className="py-2 pr-3">Percentile bootstrap CIs for the mean difference, 2,000 resamples</td></tr>
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">Bayesian sensitivity</td><td className="py-2 pr-3">Conjugate Normal Inv-Chi-Sq posterior on the mean difference, BIC-approx Bayes factor</td></tr>
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">binary outcomes</td><td className="py-2 pr-3">Two-proportion z, Wald risk-difference CI, Haldane-Anscombe-corrected odds ratio CI</td></tr>
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">multiplicity</td><td className="py-2 pr-3">Bonferroni FWER and Benjamini-Hochberg FDR at q = 0.05 across the family</td></tr>
            <tr className="border-t border-border/40"><td className="py-2 pr-3 font-mono text-xs">power</td><td className="py-2 pr-3">Pre-test sample-size and MDE for each Cohen d target</td></tr>
          </tbody>
        </table>
        <div className="mt-4 rounded-md border border-border bg-bg/40 p-4 text-sm leading-relaxed text-muted">
          <p>
            <strong className="text-text">Why not just z-tests?</strong> Rate-spread is heavy
            tailed and not Normal; Welch handles unequal variance; Mann-Whitney is robust to
            non-Normality; the permutation test makes no parametric assumption at all. A
            senior result is one where parametric, non-parametric, and resampling agree.
          </p>
          <p className="mt-3">
            <strong className="text-text">Why FDR for this family?</strong> Five tests is a
            small family but with very low p-values, FDR control is the right knob for
            screening, FWER (Bonferroni) is the strict alternative, both are reported.
          </p>
          <p className="mt-3">
            <strong className="text-text">Causal framing.</strong> HMDA omits credit score,
            full underwriting, and detailed appraisal. Every finding here is a statistical
            association in observed covariates, not a discrimination claim. The dashboard
            repeats the caveat on every card.
          </p>
          <p className="mt-3">
            <strong className="text-text">Reading the p-values.</strong> With n in the tens of
            thousands, several primary tests return p-values far below any practical threshold.
            The dashboard displays these as{" "}
            <span className="font-mono text-text">p &lt; 0.001</span> rather than figures like{" "}
            <span className="font-mono text-text">1e-102</span>, which read as noise. The exact,
            unrounded values are in the{" "}
            <a
              href={`${API_BASE}/api/results.json`}
              className="text-accent underline underline-offset-2 hover:text-text"
              target="_blank"
              rel="noreferrer"
            >
              downloadable results.json
            </a>
            .
          </p>
        </div>
      </Panel>
    </div>
  );
}

function AboutTab({ health }: { health: Health | null }) {
  return (
    <div className="mt-6 space-y-4">
      <Panel title="about" subtitle="data, stack, reproducibility">
        <div className="space-y-3 text-sm leading-relaxed text-muted">
          <p>
            <strong className="text-text">Data.</strong> CFPB FFIEC HMDA LAR for{" "}
            {health?.hmda_state ?? "MA"} {health?.hmda_year ?? 2023}. Public domain, no key.
            210,643 raw rows fetched from the Data Browser CSV endpoint and curated to first
            lien conventional owner occupied home-purchase applications.
          </p>
          <p>
            <strong className="text-text">Stack.</strong> Python 3.12, pandas, NumPy, SciPy,
            statsmodels, psycopg3, SQLAlchemy, PostgreSQL 17.5, FastAPI for the backend.
            Next.js 14, TypeScript, Tailwind, Recharts for this frontend. Backend deployed
            to a Linux VPS via systemd and nginx, frontend deployed to Cloudflare Pages.
          </p>
          <p>
            <strong className="text-text">Reproducibility.</strong> Every test is keyed to a
            fixed seed (default 20260625). The same{" "}
            <span className="font-mono text-text">flab analyze run-all</span> command
            produces deterministic output across runs. CI runs the test suite and the
            sample notebook on every push.
          </p>
          <p>
            <strong className="text-text">Limitations.</strong> Massachusetts 2023 only,
            yellow LAR fields only, no credit-score or underwriting covariates. The
            statistical disparities reported here are screening signals informing where a
            fair-lending review would dig in next, not findings of discrimination.
          </p>
        </div>
      </Panel>
    </div>
  );
}
