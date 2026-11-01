import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Beaker,
  BookOpen,
  Braces,
  Check,
  ChevronRight,
  CircleCheck,
  Clock3,
  Code2,
  FileCheck2,
  FlaskConical,
  GitCompareArrows,
  History,
  Layers3,
  LoaderCircle,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { api, download } from "./api";
import type {
  Benchmark,
  Finding,
  Generation,
  Health,
  Policy,
  PolicySnapshot,
  Run,
  RunHistoryItem,
  Scenario,
  Verdict,
} from "./types";
import { money, releaseVerdict, verdictLabels } from "./types";

type Page = "workspace" | "generation" | "policies" | "benchmarks" | "history";
const navigation = [
  { id: "workspace", label: "Verification", icon: GitCompareArrows },
  { id: "generation", label: "Test generation", icon: Sparkles },
  { id: "policies", label: "Policy library", icon: BookOpen },
  { id: "benchmarks", label: "Benchmarks", icon: FlaskConical },
  { id: "history", label: "Run history", icon: History },
] as const;
const scenarios: { id: Scenario; label: string }[] = [
  { id: "payment_date_bug", label: "Payment-date policy bug" },
  { id: "corrected", label: "Corrected update" },
  { id: "legacy_defect", label: "Legacy threshold defect corrected" },
  { id: "both_wrong", label: "Both implementations wrong" },
  { id: "execution_error", label: "Execution failure" },
];
function Badge({ verdict }: { verdict: Verdict }) {
  return <span className={`badge ${verdict}`}>{verdictLabels[verdict]}</span>;
}
function Spinner() {
  return <LoaderCircle size={16} className="spin" aria-hidden="true" />;
}
function ReleaseAdvisory({
  run,
  label,
  compact = false,
}: {
  run: RunHistoryItem;
  label: string;
  compact?: boolean;
}) {
  const release = releaseVerdict(run);
  return (
    <span aria-label={label}>
      <strong className={`decision ${release.outcome.toLowerCase()}`}>
        {release.outcome}
      </strong>
      {!compact && <> · {release.reason} No automatic release approval.</>}
    </span>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>("workspace");
  const [health, setHealth] = useState<Health | null>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [bundledPolicies, setBundledPolicies] = useState<Policy[]>([]);
  const [policySnapshots, setPolicySnapshots] = useState<PolicySnapshot[]>([]);
  const [scenario, setScenario] = useState<Scenario>("payment_date_bug");
  const [sources, setSources] = useState({ java: "", python: "" });
  const [customSource, setCustomSource] = useState(false);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [fixtureReady, setFixtureReady] = useState(false);
  const [mode, setMode] = useState<"simulator" | "modal">("simulator");
  const [generationMode, setGenerationMode] = useState<"offline" | "meta">(
    "offline",
  );
  const [count, setCount] = useState(16);
  const [suite, setSuite] = useState<Generation | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [selected, setSelected] = useState<Finding | null>(null);
  const [filter, setFilter] = useState("all");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [releaseOpen, setReleaseOpen] = useState(false);
  const [history, setHistory] = useState<RunHistoryItem[]>([]);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [policyJSON, setPolicyJSON] = useState("");
  const [policyEditor, setPolicyEditor] = useState(false);
  const [policySetId, setPolicySetId] = useState<string | null>(null);
  const metaReady =
    health?.integrations.meta.enabled && health?.integrations.meta.configured;
  const modalReady =
    health?.integrations.modal.enabled && health?.integrations.modal.configured;

  useEffect(() => {
    let active = true;
    Promise.all([
      api<Health>("/health"),
      api<{ policies: Policy[] }>("/policies"),
      api<PolicySnapshot[]>("/policy-sets"),
    ])
      .then(([status, library, snapshots]) => {
        if (active) {
          setHealth(status);
          setPolicies(library.policies);
          setBundledPolicies(library.policies);
          setPolicySnapshots(snapshots);
          setPolicyJSON(JSON.stringify(library, null, 2));
        }
      })
      .catch(() => {
        if (active)
          setError(
            "Backend unavailable. The local API must be running on port 8000.",
          );
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    let active = true;
    setFixtureReady(false);
    api<{ sources: { java: string; python: string } }>(`/fixtures/${scenario}`)
      .then((data) => {
        if (active) {
          setSources(data.sources);
          setCustomSource(false);
          setSuite(null);
          setFixtureReady(true);
        }
      })
      .catch(() => {
        if (active) setError("Could not load the selected fixture.");
      });
    return () => {
      active = false;
    };
  }, [scenario]);
  useEffect(() => {
    const visible =
      run?.findings.filter(
        (finding) => filter === "all" || finding.verdict === filter,
      ) ?? [];
    setSelected(
      (current) =>
        visible.find((finding) => finding.case_id === current?.case_id) ??
        visible[0] ??
        null,
    );
  }, [run, filter]);
  useEffect(() => {
    if (page === "history")
      api<RunHistoryItem[]>("/runs")
        .then(setHistory)
        .catch(() => setError("Could not load saved runs."));
    if (page === "benchmarks")
      api<Benchmark>("/benchmarks")
        .then(setBenchmark)
        .catch(() => setError("Could not load benchmark results."));
  }, [page]);
  async function action(label: string, work: () => Promise<void>) {
    setBusy(label);
    setError("");
    setNotice("");
    try {
      await work();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The operation failed.");
    } finally {
      setBusy("");
    }
  }
  const sourcePayload = customSource
    ? { java_source: sources.java, python_source: sources.python }
    : {};
  async function generate() {
    await action("generate", async () => {
      const data = await api<Generation>("/generate", {
        mode: generationMode,
        count,
        scenario,
        policy_set_id: policySetId,
        ...sourcePayload,
      });
      setSuite(data);
      setNotice(
        `${data.suite.cases.length} validated test hypotheses are ready.`,
      );
    });
  }
  async function verify() {
    if (customSource && mode !== "modal") {
      setError(
        "Edited source requires approved Modal execution. Reset the fixture to use the local simulator.",
      );
      return;
    }
    await action("verify", async () => {
      const data = await api<Run>("/verify", {
        scenario,
        mode,
        generation_id: suite?.id ?? null,
        policy_set_id: policySetId,
        ...sourcePayload,
      });
      setRun(data);
      setSelected(
        data.findings.find((f) => f.verdict === "unauthorized_regression") ??
          data.findings[0],
      );
      setFilter("all");
      setPage("workspace");
    });
  }
  async function replay() {
    if (!run) return;
    await action("replay", async () => {
      const result = await api<{ consistent: boolean; note: string }>(
        `/runs/${run.id}/replay`,
        {},
      );
      if (!result.consistent)
        throw new Error(
          "Replay found inconsistent evidence. Review the saved report.",
        );
      setNotice(
        `Evidence replay consistent. Release verdict: ${releaseVerdict(run).outcome}. ${result.note} Replay does not re-execute code or grant release approval.`,
      );
    });
  }
  const findings =
    run?.findings.filter((f) => filter === "all" || f.verdict === filter) ?? [];
  const selectedPolicy = run?.policies.policies.find(
    (p) => p.id === selected?.oracle?.policy_id,
  );
  const disabled = Boolean(busy) || !health || !fixtureReady;

  function selectPolicySnapshot(id: string) {
    const chosen = id
      ? policySnapshots.find((snapshot) => snapshot.id === id)?.policies
          .policies
      : bundledPolicies;
    if (!chosen) return;
    setPolicySetId(id || null);
    setPolicies(chosen);
    setPolicyJSON(JSON.stringify({ policies: chosen }, null, 2));
    setSuite(null);
    setPolicyEditor(false);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" inert={releaseOpen}>
        <a
          className="brand"
          href="#workspace"
          onClick={() => setPage("workspace")}
          aria-label="RuleReplay home"
        >
          <span className="brand-mark">
            <Layers3 size={23} />
          </span>
          <span>
            RuleReplay<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="team-label">BEYOND ASSERTIONS</div>
        <div className="project-switch">
          <span className="project-symbol">
            <Braces size={18} />
          </span>
          <div>
            <strong>Loan servicing</strong>
            <small>Verification project</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <button
              key={item.id}
              className={page === item.id ? "nav-item active" : "nav-item"}
              onClick={() => setPage(item.id)}
              aria-current={page === item.id ? "page" : undefined}
            >
              <item.icon size={18} />
              {item.label}
              {item.id === "workspace" && run && (
                <span className="nav-count">{run.summary.total}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-status">
            <span className={health ? "status-dot" : "status-dot off"} />
            {health ? "Local environment connected" : "Connecting to local API"}
          </div>
          <p>Synthetic data. Real policy checks.</p>
          <div className="hackathon-label">
            META GLOBAL AI
            <br />
            <strong>DEVELOPER HACKATHON 2026</strong>
          </div>
        </div>
      </aside>
      <div className="main-shell" inert={releaseOpen}>
        <header className="topbar">
          <div>
            <span className="muted">Loan servicing</span>
            <ChevronRight size={14} />
            <strong>
              {navigation.find((item) => item.id === page)?.label}
            </strong>
          </div>
          <div>
            <span className="environment-pill">
              <span className="status-dot" />
              Local workspace
            </span>
            <span className="avatar">BA</span>
          </div>
        </header>
        <main>
          {error && !releaseOpen && (
            <div role="alert" className="banner error">
              <Activity size={18} />
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {notice && !releaseOpen && (
            <div role="status" className="banner success">
              <CircleCheck size={18} />
              <span>{notice}</span>
              <button aria-label="Dismiss notice" onClick={() => setNotice("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {page === "workspace" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    <span className="tiny-line" />
                    BEHAVIORAL VERIFICATION
                  </div>
                  <h1>
                    Every change. Every rule.
                    <br />
                    <span>Evidence you can replay.</span>
                  </h1>
                  <p>
                    Your code passed the tests. But did it follow the rules?
                  </p>
                </div>
                <button
                  className="button secondary"
                  disabled={!run}
                  onClick={() => setReleaseOpen(true)}
                >
                  <FileCheck2 size={16} />
                  Release summary
                </button>
              </div>
              <section
                className="workflow-card"
                aria-label="Verification workflow"
              >
                <div className="workflow-step">
                  <span className="step-icon">
                    <Code2 size={20} />
                  </span>
                  <div>
                    <span className="eyebrow">01 / BASELINE</span>
                    <strong>Legacy implementation</strong>
                    <small>Java · five-day grace period</small>
                  </div>
                </div>
                <ArrowRight className="flow-arrow" size={20} />
                <div className="workflow-step oracle-step">
                  <span className="step-icon">
                    <ShieldCheck size={21} />
                  </span>
                  <div>
                    <span className="eyebrow">INDEPENDENT AUTHORITY</span>
                    <strong>Approved policy oracle</strong>
                    <small>Versioned rules · deterministic cents</small>
                  </div>
                </div>
                <ArrowRight className="flow-arrow" size={20} />
                <div className="workflow-step">
                  <span className="step-icon">
                    <Braces size={20} />
                  </span>
                  <div>
                    <span className="eyebrow">02 / CANDIDATE</span>
                    <strong>Updated implementation</strong>
                    <small>Python · policy transition</small>
                  </div>
                </div>
              </section>
              <div className="draft-context">
                <strong>Current draft</strong>
                <span>
                  {policySetId
                    ? `Policy snapshot ${policySetId.slice(0, 8)}`
                    : "Bundled policy snapshot"}{" "}
                  · changes apply to the next verification
                </span>
              </div>
              <section
                className="run-toolbar"
                aria-label="Current draft configuration"
              >
                <label>
                  Scenario
                  <select
                    value={scenario}
                    disabled={Boolean(busy)}
                    onChange={(e) => {
                      setScenario(e.target.value as Scenario);
                      setFixtureReady(false);
                      setSuite(null);
                    }}
                  >
                    {scenarios.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Execution
                  <select
                    value={mode}
                    disabled={Boolean(busy)}
                    onChange={(e) =>
                      setMode(e.target.value as "simulator" | "modal")
                    }
                  >
                    <option value="simulator">Trusted fixture simulator</option>
                    <option value="modal" disabled={!modalReady}>
                      Modal Sandboxes{!modalReady ? " · approval required" : ""}
                    </option>
                  </select>
                </label>
                <div className="test-count">
                  <strong>{suite?.suite.cases.length ?? 16}</strong> boundary
                  cases ·{" "}
                  <button
                    className="text-link"
                    onClick={() => setPage("generation")}
                  >
                    Configure
                  </button>
                </div>
                <button
                  className="button primary"
                  disabled={disabled}
                  onClick={verify}
                >
                  {busy === "verify" ? <Spinner /> : <Play size={16} />}{" "}
                  {busy === "verify" ? "Verifying…" : "Run current draft"}
                </button>
              </section>
              <div className="mode-note">
                <Beaker size={14} />
                {mode === "simulator"
                  ? "Local demo uses reviewed fixture behavior. No submitted code is executed and no cloud request is made."
                  : "Live execution creates isolated, billable Modal Sandboxes for each implementation and case."}
              </div>
              {run && (
                <section
                  className="saved-run-context"
                  aria-label="Saved run context"
                >
                  <div>
                    <strong>Saved verification {run.id.slice(0, 8)}</strong>
                    <span>
                      {
                        scenarios.find((item) => item.id === run.scenario)
                          ?.label
                      }{" "}
                      ·{" "}
                      {run.execution_mode === "modal"
                        ? "Modal Sandboxes"
                        : "Trusted fixture simulator"}
                    </span>
                  </div>
                  <p>
                    <ReleaseAdvisory run={run} label="Verification advisory" />
                  </p>
                  <p>
                    <code>{run.id}</code> · Test source:{" "}
                    {run.test_source ?? "Historical record"}
                  </p>
                  {run.metrics && (
                    <p>
                      {run.lifecycle?.state} ·{" "}
                      {run.metrics.duration_ms.toFixed(1)} ms ·{" "}
                      {run.metrics.sandbox_executions} sandbox executions ·
                      Correlation: <code>{run.correlation_id}</code>
                    </p>
                  )}
                  <p>
                    {run.execution_note} The findings and evidence below use
                    this run’s saved source and policy snapshots.
                  </p>
                </section>
              )}
              <section className="metrics" aria-label="Run metrics">
                <Metric
                  label="Cases evaluated"
                  value={run?.summary.total}
                  caption="Unique inputs evaluated"
                  icon={<GitCompareArrows size={18} />}
                />
                <Metric
                  label="Release blockers"
                  value={run?.summary.blockers}
                  caption="Regressions, failures or both wrong"
                  icon={<Activity size={18} />}
                  tone={run?.summary.blockers ? "red" : ""}
                />
                <Metric
                  label="Authorized changes"
                  value={run?.summary.counts.authorized_policy_change}
                  caption="Supported by policy provenance"
                  icon={<ShieldCheck size={18} />}
                  tone="green"
                />
                <Metric
                  label="Needs review"
                  value={run?.summary.unresolved}
                  caption="Missing evidence or invalid input"
                  icon={<Clock3 size={18} />}
                  tone="amber"
                />
              </section>
              {run ? (
                <section className="results-grid">
                  <div className="panel findings-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>
                          Verification findings{" "}
                          <span className="count-tag">{run.summary.total}</span>
                        </h2>
                        <p>
                          Case findings against the approved rule; release
                          verdict above.
                        </p>
                      </div>
                      <button
                        className="icon-button"
                        title="Replay saved evidence"
                        aria-label="Replay saved evidence"
                        onClick={replay}
                        disabled={disabled}
                      >
                        {busy === "replay" ? (
                          <Spinner />
                        ) : (
                          <RefreshCw size={17} />
                        )}
                      </button>
                    </div>
                    <div className="filter-row">
                      <label className="sr-only" htmlFor="finding-filter">
                        Filter findings
                      </label>
                      <select
                        id="finding-filter"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                      >
                        <option value="all">All findings</option>
                        {Object.entries(verdictLabels).map(([key, label]) => (
                          <option key={key} value={key}>
                            {label} ({run.summary.counts[key as Verdict]})
                          </option>
                        ))}
                      </select>
                      <span>{findings.length} cases</span>
                    </div>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>Case / due date</th>
                            <th>Legacy</th>
                            <th>Updated</th>
                            <th>Finding</th>
                          </tr>
                        </thead>
                        <tbody>
                          {findings.map((f) => (
                            <tr
                              key={f.case_id}
                              className={
                                selected?.case_id === f.case_id
                                  ? "selected"
                                  : ""
                              }
                            >
                              <td>
                                <button
                                  className="case-button"
                                  onClick={() => setSelected(f)}
                                  aria-label={`Inspect ${f.case_id}`}
                                >
                                  <strong>{f.case_id}</strong>
                                  <small>
                                    {f.case?.due_date ?? "Invalid case"}
                                  </small>
                                </button>
                              </td>
                              <td className="amount">
                                {money(f.legacy?.fee_cents)}
                              </td>
                              <td
                                className={
                                  f.updated?.fee_cents !== f.oracle?.fee_cents
                                    ? "amount bad-amount"
                                    : "amount"
                                }
                              >
                                {money(f.updated?.fee_cents)}
                              </td>
                              <td>
                                <Badge verdict={f.verdict} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {findings.length === 0 && (
                        <div className="empty-small">
                          No findings match this filter.
                        </div>
                      )}
                    </div>
                    <div className="table-footer">
                      <span className="status-dot" />
                      Evidence saved locally <code>{run.id.slice(0, 8)}</code>
                      <span>{run.duplicates_removed} duplicates removed</span>
                    </div>
                  </div>
                  <aside
                    className="panel evidence-panel"
                    aria-label="Policy-backed evidence"
                  >
                    {selected && (
                      <>
                        <div className="panel-heading">
                          <div className="flex items-center gap-2">
                            <ShieldCheck size={18} />
                            <h2>Policy-backed evidence</h2>
                          </div>
                          <span className="eyebrow">{selected.case_id}</span>
                        </div>
                        <div className="evidence-content">
                          <Badge verdict={selected.verdict} />
                          <h3>{verdictLabels[selected.verdict]}</h3>
                          <p>{selected.reason}</p>
                          <div className="case-dates">
                            <div>
                              <span>LOAN DUE DATE</span>
                              <strong>{selected.case?.due_date ?? "—"}</strong>
                            </div>
                            <div>
                              <span>PAYMENT DATE</span>
                              <strong>
                                {selected.case?.payment_date ?? "—"}
                              </strong>
                            </div>
                          </div>
                          <div className="expected-result">
                            <span>Policy expects</span>
                            <strong>{money(selected.oracle?.fee_cents)}</strong>
                            <small>
                              {selected.oracle?.days_late ?? "—"} days late ·{" "}
                              {selected.oracle?.grace_days ?? "—"}-day grace
                            </small>
                          </div>
                          <p className="calculation">
                            {selected.oracle?.explanation ??
                              "The input could not be evaluated."}
                          </p>
                          {selectedPolicy && (
                            <div className="policy-citation">
                              <div>
                                <BookOpen size={15} />
                                <strong>{selectedPolicy.id}</strong>
                                <span>Approved</span>
                              </div>
                              <blockquote>
                                {selectedPolicy.provenance.clause}
                              </blockquote>
                              <small>
                                {selectedPolicy.provenance.document}
                                <br />
                                Approved {selectedPolicy.provenance.approved_on}
                              </small>
                            </div>
                          )}
                          {selected.legacy?.error && (
                            <p className="error-text">
                              Legacy: {selected.legacy.error}
                            </p>
                          )}
                          {selected.updated?.error && (
                            <p className="error-text">
                              Updated: {selected.updated.error}
                            </p>
                          )}
                          {run.execution_mode === "simulator" &&
                            [
                              "unauthorized_regression",
                              "both_implementations_wrong",
                            ].includes(selected.verdict) && (
                              <button
                                className="text-link minimize-button"
                                disabled={disabled}
                                onClick={() =>
                                  action("minimize", async () => {
                                    const result = await api<{
                                      case: {
                                        due_date: string;
                                        payment_date: string;
                                      };
                                      checked: number;
                                    }>(
                                      `/runs/${run.id}/minimize/${selected.case_id}`,
                                      {},
                                    );
                                    setNotice(
                                      `Minimal delay preserving this finding: due ${result.case.due_date}, paid ${result.case.payment_date}. ${result.checked} candidates checked locally.`,
                                    );
                                  })
                                }
                              >
                                Minimize counterexample <ArrowRight size={14} />
                              </button>
                            )}
                          <div className="evidence-footnote">
                            <Check size={14} />
                            Expected values calculated independently of AI.
                          </div>
                          <div className="source-fingerprints">
                            <span>Source fingerprints</span>
                            <code>
                              Java {run.source_sha256?.java?.slice(0, 12)} ·
                              Python {run.source_sha256?.python?.slice(0, 12)}
                            </code>
                          </div>
                        </div>
                      </>
                    )}
                    {!selected && (
                      <div className="empty-small">
                        Select a matching finding to inspect its policy
                        evidence.
                      </div>
                    )}
                  </aside>
                </section>
              ) : (
                <section className="empty-state panel">
                  <div className="empty-orbit">
                    <GitCompareArrows size={30} />
                  </div>
                  <h2>Find what ordinary assertions miss.</h2>
                  <p>
                    Replay a boundary-focused suite against the legacy code, the
                    update, and the approved policy. Every finding comes with
                    its evidence.
                  </p>
                  <button
                    className="text-link"
                    onClick={verify}
                    disabled={disabled}
                  >
                    Start with the payment-date bug <ArrowRight size={15} />
                  </button>
                </section>
              )}
              {run && (
                <section className="panel source-panel saved-snapshot">
                  <details>
                    <summary>
                      Saved source and policy snapshot{" "}
                      <code>{run.id.slice(0, 8)}</code>
                    </summary>
                    <p className="snapshot-note">
                      Read-only evidence captured for this run. Editing the
                      current draft does not change this report.
                    </p>
                    <div className="source-editors">
                      {(["java", "python"] as const).map((language) => (
                        <label key={language}>
                          Saved{" "}
                          {language === "java" ? "LegacyLoan.java" : "loan.py"}
                          <textarea
                            readOnly
                            aria-label={`Saved ${language} source`}
                            value={run.sources[language]}
                            spellCheck={false}
                          />
                        </label>
                      ))}
                    </div>
                    <div className="saved-policy-list">
                      {run.policies.policies.map((policy) => (
                        <div key={policy.id}>
                          <strong>
                            {policy.id} · {policy.status} · {policy.grace_days}
                            -day grace · {money(policy.fee_cents)}
                          </strong>
                          <small>
                            Due dates {policy.effective_from} →{" "}
                            {policy.effective_until ?? "onward"} ·{" "}
                            {policy.provenance.document}
                          </small>
                          <blockquote>{policy.provenance.clause}</blockquote>
                        </div>
                      ))}
                      <code className="hash">
                        Policy SHA-256: {run.policy_sha256}
                      </code>
                    </div>
                  </details>
                </section>
              )}
              <section className="panel source-panel">
                <button
                  className="source-toggle"
                  aria-expanded={sourceOpen}
                  onClick={() => setSourceOpen(!sourceOpen)}
                >
                  <Code2 size={17} />
                  <strong>Current draft implementation sources</strong>
                  <span>
                    {customSource
                      ? "Edited source · Modal required"
                      : "Reviewed synthetic fixtures"}
                  </span>
                  <ChevronRight
                    size={16}
                    className={sourceOpen ? "rotated" : ""}
                  />
                </button>
                {sourceOpen && (
                  <>
                    <div className="source-editors">
                      {(["java", "python"] as const).map((language) => (
                        <label key={language}>
                          {language === "java" ? "LegacyLoan.java" : "loan.py"}
                          <textarea
                            spellCheck={false}
                            aria-label={`${language} source`}
                            value={sources[language]}
                            onChange={(e) => {
                              setSources({
                                ...sources,
                                [language]: e.target.value,
                              });
                              setCustomSource(true);
                              setSuite(null);
                            }}
                          />
                        </label>
                      ))}
                    </div>
                    {customSource && (
                      <button
                        className="button secondary reset-source"
                        onClick={() =>
                          action("reset", async () => {
                            const result = await api<{
                              sources: typeof sources;
                            }>(`/fixtures/${scenario}`);
                            setSources(result.sources);
                            setCustomSource(false);
                            setSuite(null);
                          })
                        }
                      >
                        Reset to reviewed fixture
                      </button>
                    )}
                  </>
                )}
              </section>
            </>
          )}
          {page === "generation" && (
            <>
              <PageHeading
                eyebrow="HYPOTHESES, NOT VERDICTS"
                title="Test the boundaries."
                text="Muse Wonder analyzes code and policy to suggest high-value inputs. The oracle owns every expected result."
              />
              <div className="generation-grid">
                <section className="panel padded">
                  <div className="section-icon">
                    <Sparkles size={22} />
                  </div>
                  <h2>Generate test hypotheses</h2>
                  <p className="muted">
                    Focus on policy transitions, exact grace days, calendar
                    edges and missing evidence.
                  </p>
                  <label className="field">
                    Generation provider
                    <select
                      value={generationMode}
                      onChange={(e) =>
                        setGenerationMode(e.target.value as "offline" | "meta")
                      }
                    >
                      <option value="offline">
                        Offline deterministic boundaries
                      </option>
                      <option value="meta" disabled={!metaReady}>
                        Meta Muse Wonder
                        {!metaReady ? " · approval required" : ""}
                      </option>
                    </select>
                  </label>
                  <label className="field">
                    Case budget
                    <select
                      value={count}
                      onChange={(e) => setCount(Number(e.target.value))}
                    >
                      {[8, 16, 24, 48].map((n) => (
                        <option key={n} value={n}>
                          {n} cases
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="info-box">
                    <ShieldCheck size={18} />
                    <p>
                      {generationMode === "offline"
                        ? "Offline mode is a deterministic boundary generator. It does not call or imitate Meta AI."
                        : "One billable request to muse-wonder-1.0. No automatic retries. Code and approved policies are sent to Meta."}
                    </p>
                  </div>
                  <button
                    className="button primary full-width"
                    disabled={disabled}
                    onClick={generate}
                  >
                    {busy === "generate" ? <Spinner /> : <Sparkles size={16} />}
                    Generate hypotheses
                  </button>
                  <p className="fine-print">
                    Primary model:{" "}
                    {health?.integrations.model ?? "muse-wonder-1.0"}
                    <br />
                    {metaReady
                      ? "Meta configured and enabled."
                      : "Live Meta generation is disabled until credentials and approval are supplied."}
                  </p>
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>
                        {suite
                          ? `${suite.suite.cases.length} validated hypotheses`
                          : "Your next test suite"}
                      </h2>
                      <p>
                        {suite
                          ? suite.suite.source.replaceAll("_", " ")
                          : "Generation results will appear here."}
                      </p>
                    </div>
                    {suite && (
                      <button
                        className="button secondary"
                        onClick={verify}
                        disabled={disabled}
                      >
                        <Play size={14} />
                        Verify suite
                      </button>
                    )}
                  </div>
                  {suite ? (
                    <>
                      <div className="suite-analysis">
                        {suite.suite.analysis}
                        <small>
                          {suite.suite.rejected_count} invalid candidates
                          rejected · {suite.suite.duplicate_count} duplicates
                          removed
                        </small>
                      </div>
                      <div className="table-scroll">
                        <table>
                          <thead>
                            <tr>
                              <th>Hypothesis</th>
                              <th>Due date</th>
                              <th>Payment date</th>
                            </tr>
                          </thead>
                          <tbody>
                            {suite.suite.cases.map((c) => (
                              <tr key={c.id}>
                                <td>
                                  <strong>{c.id}</strong>
                                  <small className="rationale">
                                    {c.rationale}
                                  </small>
                                </td>
                                <td className="date-cell">{c.due_date}</td>
                                <td className="date-cell">{c.payment_date}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : (
                    <div className="empty-state compact">
                      <Beaker size={36} />
                      <h3>Start with an edge case.</h3>
                      <p>
                        Every generated input is schema-validated and
                        deduplicated before execution.
                      </p>
                    </div>
                  )}
                </section>
              </div>
            </>
          )}
          {page === "policies" && (
            <>
              <PageHeading
                eyebrow="THE SOURCE OF AUTHORITY"
                title="Rules with a history."
                text="Immutable policy snapshots, explicit effective dates, and the approval evidence behind every calculation."
              />
              <div className="policy-banner">
                <ShieldCheck size={22} />
                <div>
                  <strong>
                    Policy selection is based on the loan due date.
                  </strong>
                  <p>
                    A payment after November 1 does not move an earlier loan
                    into the new grace period.
                  </p>
                </div>
                <span className="badge compliant">Synthetic demo policies</span>
              </div>
              <section className="panel padded snapshot-selector">
                <label className="field">
                  Policy snapshot for the current draft
                  <select
                    value={policySetId ?? ""}
                    disabled={Boolean(busy)}
                    onChange={(event) =>
                      selectPolicySnapshot(event.target.value)
                    }
                  >
                    <option value="">Bundled approved policies</option>
                    {policySnapshots.map((snapshot) => (
                      <option key={snapshot.id} value={snapshot.id}>
                        Snapshot {snapshot.id.slice(0, 8)} ·{" "}
                        {new Date(snapshot.created_at).toLocaleString()}
                      </option>
                    ))}
                  </select>
                </label>
                <p>
                  Saved snapshots remain available after reload. This selection
                  applies to future runs; saved evidence retains its original
                  policies.
                </p>
              </section>
              <div className="policy-grid">
                {policies.map((p) => (
                  <section className="panel policy-card" key={p.id}>
                    <div className="policy-card-top">
                      <span className="version-label">V{p.version}</span>
                      <span className="badge compliant">{p.status}</span>
                    </div>
                    <h2>{p.name}</h2>
                    <code>{p.id}</code>
                    <div className="policy-numbers">
                      <div>
                        <strong>
                          {p.grace_days}
                          <small>days</small>
                        </strong>
                        <span>Grace period</span>
                      </div>
                      <div>
                        <strong>{money(p.fee_cents)}</strong>
                        <span>Single late fee</span>
                      </div>
                    </div>
                    <dl>
                      <dt>Effective due dates</dt>
                      <dd>
                        {p.effective_from} →{" "}
                        {p.effective_until
                          ? `${p.effective_until} (exclusive)`
                          : "onward"}
                      </dd>
                      <dt>Approved by</dt>
                      <dd>{p.provenance.approved_by}</dd>
                      <dt>Approved on</dt>
                      <dd>{p.provenance.approved_on}</dd>
                      <dt>Source</dt>
                      <dd>{p.provenance.document}</dd>
                    </dl>
                    <blockquote>{p.provenance.clause}</blockquote>
                  </section>
                ))}
              </div>
              <section className="panel padded">
                <div className="section-row">
                  <div>
                    <h2>Versioned policy management</h2>
                    <p className="muted">
                      Save a new validated snapshot. Existing policy evidence
                      remains immutable.
                    </p>
                  </div>
                  <button
                    className="button secondary"
                    onClick={() => setPolicyEditor(!policyEditor)}
                  >
                    <BookOpen size={16} />
                    {policyEditor ? "Close editor" : "Edit a new snapshot"}
                  </button>
                </div>
                {policyEditor && (
                  <>
                    <label className="field">
                      Policy snapshot JSON
                      <textarea
                        className="policy-json"
                        value={policyJSON}
                        onChange={(e) => setPolicyJSON(e.target.value)}
                        spellCheck={false}
                      />
                    </label>
                    <button
                      className="button primary"
                      disabled={disabled}
                      onClick={() =>
                        action("policy", async () => {
                          const parsed = JSON.parse(policyJSON);
                          const result = await api<PolicySnapshot>(
                            "/policy-sets",
                            parsed,
                          );
                          setPolicySetId(result.id);
                          setPolicies(result.policies.policies);
                          setPolicySnapshots((snapshots) => [
                            result,
                            ...snapshots,
                          ]);
                          setPolicyJSON(
                            JSON.stringify(result.policies, null, 2),
                          );
                          setSuite(null);
                          setNotice(
                            "New immutable policy snapshot saved and selected for subsequent runs.",
                          );
                          setPolicyEditor(false);
                        })
                      }
                    >
                      Validate and save snapshot
                    </button>
                  </>
                )}
                {policySetId && (
                  <p className="fine-print">
                    Active custom snapshot: {policySetId}
                  </p>
                )}
              </section>
            </>
          )}
          {page === "benchmarks" && (
            <>
              <PageHeading
                eyebrow="MEASURED, NOT ASSUMED"
                title="Put the method to the test."
                text="Seeded synthetic defects, reproducible test budgets, and honest limits on what has been measured."
              />
              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>Defect detection comparison</h2>
                    <p>
                      Fixed seed {benchmark?.seed ?? "—"} · independent
                      approved-policy oracle
                    </p>
                  </div>
                  <span className="badge compliant">Local measurements</span>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Method</th>
                        <th>Cases</th>
                        <th>Defects found</th>
                        <th>False alarms</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmark?.rows?.map((row) => (
                        <tr key={row.method}>
                          <td>
                            <strong>{row.method}</strong>
                          </td>
                          <td>{row.cases ?? "—"}</td>
                          <td>
                            {row.detected == null
                              ? "—"
                              : `${row.detected} / ${row.total_defects}`}
                          </td>
                          <td>{row.false_alarms ?? "—"}</td>
                          <td>{row.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {(!benchmark || benchmark.status === "not_run") && (
                  <div className="empty-small">
                    No benchmark measurements are available yet.
                  </div>
                )}
              </section>
              <div className="info-box benchmark-note">
                <Beaker size={22} />
                <div>
                  <strong>AI results require actual AI runs.</strong>
                  <p>
                    Offline targeted boundary results are an in-sample,
                    known-defect benchmark with tuning. They do not measure Muse
                    Wonder performance or establish AI superiority.
                  </p>
                  {benchmark?.limitations?.map((text, i) => (
                    <p key={i}>{text}</p>
                  ))}
                </div>
              </div>
              <section className="panel">
                <div className="panel-heading">
                  <h2>Synthetic defect catalog</h2>
                </div>
                <div className="defect-grid">
                  {benchmark?.defects?.map((d) => (
                    <div key={d.id}>
                      <code>{d.id}</code>
                      <strong>{d.description}</strong>
                      <small>
                        {d.detected_by.length
                          ? `Found by: ${d.detected_by.join(", ")}`
                          : "Not detected in measured suites"}
                      </small>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
          {page === "history" && (
            <>
              <PageHeading
                eyebrow="REPRODUCIBLE EVIDENCE"
                title="Every run leaves a record."
                text="Return to the exact policies, implementation hashes, observations and deterministic verdicts of a saved run."
              />
              <section className="panel">
                <div className="panel-heading">
                  <h2>Recent verification runs</h2>
                  <span>{history.length} saved</span>
                </div>
                {history.length ? (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Run</th>
                          <th>Scenario</th>
                          <th>Cases</th>
                          <th>Release verdict</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((item) => (
                          <tr key={item.id}>
                            <td>
                              <code>{item.id.slice(0, 8)}</code>
                              <small>
                                {new Date(item.created_at).toLocaleString()}
                              </small>
                            </td>
                            <td>
                              {
                                scenarios.find((s) => s.id === item.scenario)
                                  ?.label
                              }
                              <small>{item.execution_mode}</small>
                            </td>
                            <td>{item.summary.total}</td>
                            <td>
                              <ReleaseAdvisory
                                run={item}
                                label="Historical release verdict"
                                compact
                              />
                            </td>
                            <td>
                              <button
                                className="text-link"
                                disabled={disabled}
                                onClick={() =>
                                  action("load", async () => {
                                    const data = await api<Run>(
                                      `/runs/${item.id}`,
                                    );
                                    setRun(data);
                                    setSelected(data.findings[0]);
                                    setFilter("all");
                                    setPage("workspace");
                                  })
                                }
                              >
                                Open evidence <ArrowRight size={14} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-state compact">
                    <History size={32} />
                    <h3>No saved runs yet.</h3>
                    <p>
                      Run a verification to create your first replayable
                      evidence record.
                    </p>
                  </div>
                )}
              </section>
            </>
          )}
          <footer>
            <span>
              RuleReplay <span className="muted">/</span> Beyond Assertions
            </span>
            <span>
              Synthetic policies · Independent oracle · Evidence first
            </span>
          </footer>
        </main>
      </div>
      {releaseOpen && run && (
        <div className="modal-backdrop" onClick={() => setReleaseOpen(false)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="release-title"
            className="release-dialog"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Escape") setReleaseOpen(false);
              if (e.key === "Tab") {
                const buttons = Array.from(
                  e.currentTarget.querySelectorAll<HTMLButtonElement>(
                    "button:not(:disabled)",
                  ),
                );
                const first = buttons[0];
                const last = buttons[buttons.length - 1];
                if (e.shiftKey && document.activeElement === first) {
                  e.preventDefault();
                  last?.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                  e.preventDefault();
                  first?.focus();
                }
              }
            }}
          >
            <div className="panel-heading">
              <h2 id="release-title">Release verification summary</h2>
              <button
                className="icon-button"
                autoFocus
                aria-label="Close release summary"
                onClick={() => setReleaseOpen(false)}
              >
                <X size={20} />
              </button>
            </div>
            <div className="padded">
              {error && (
                <div role="alert" className="banner error">
                  {error}
                </div>
              )}
              {notice && (
                <div role="status" className="banner success">
                  {notice}
                </div>
              )}
              <p>
                <ReleaseAdvisory run={run} label="Release advisory" />
              </p>
              <h3>
                {run.summary.blockers} blockers. {run.summary.unresolved}{" "}
                unresolved.
              </h3>
              <p>{run.summary.scope}</p>
              <dl>
                {Object.entries(run.summary.counts).map(([key, value]) => (
                  <div className="summary-line" key={key}>
                    <dt>{verdictLabels[key as Verdict]}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
              <div className="info-box">
                <ShieldCheck size={20} />
                <p>
                  {run.execution_note} Report hash:{" "}
                  <code className="hash">{run.integrity_sha256}</code>
                </p>
              </div>
              <div className="dialog-actions">
                <button
                  className="button secondary"
                  onClick={replay}
                  disabled={disabled}
                >
                  <RefreshCw size={15} />
                  Replay evidence
                </button>
                <button
                  className="button primary"
                  onClick={() =>
                    action("export", async () => {
                      const data = await api<Run>(`/runs/${run.id}`);
                      download(
                        `rulereplay-${run.id.slice(0, 8)}.json`,
                        JSON.stringify(data, null, 2),
                      );
                    })
                  }
                  disabled={disabled}
                >
                  <ArrowDownToLine size={15} />
                  Export evidence
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
function Metric({
  label,
  value,
  caption,
  icon,
  tone = "",
}: {
  label: string;
  value?: number;
  caption: string;
  icon: ReactNode;
  tone?: string;
}) {
  return (
    <div className={`metric ${tone}`}>
      <div>
        <span>{label}</span>
        {icon}
      </div>
      <strong>{value ?? "—"}</strong>
      <small>{caption}</small>
    </div>
  );
}
function PageHeading({
  eyebrow,
  title,
  text,
}: {
  eyebrow: string;
  title: string;
  text: string;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">
          <span className="tiny-line" />
          {eyebrow}
        </div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
    </div>
  );
}
