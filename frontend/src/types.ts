export type Scenario =
  | "payment_date_bug"
  | "corrected"
  | "legacy_defect"
  | "both_wrong"
  | "execution_error";
export type Verdict =
  | "compliant"
  | "unauthorized_regression"
  | "authorized_policy_change"
  | "corrected_legacy_defect"
  | "both_implementations_wrong"
  | "insufficient_policy_evidence"
  | "invalid_input"
  | "execution_failure";
export interface TestCase {
  id: string;
  due_date: string;
  payment_date: string;
  rationale: string;
}
export interface Policy {
  id: string;
  name: string;
  version: number;
  status: string;
  effective_from: string;
  effective_until: string | null;
  grace_days: number;
  fee_cents: number;
  selection_basis: string;
  supersedes: string | null;
  provenance: {
    document: string;
    clause: string;
    approved_by: string;
    approved_on: string;
    change_reason: string;
  };
}
export interface Health {
  status: string;
  integrations: {
    model: string;
    meta: { enabled: boolean; configured: boolean };
    modal: { enabled: boolean; configured: boolean };
  };
}
export interface Observation {
  status: string;
  fee_cents: number | null;
  error: string | null;
}
export interface Finding {
  case_id: string;
  case: TestCase | null;
  verdict: Verdict;
  reason: string;
  legacy: Observation | null;
  updated: Observation | null;
  oracle: {
    fee_cents: number | null;
    policy_id: string | null;
    days_late: number;
    grace_days: number | null;
    explanation: string;
    predecessor_policy_id: string | null;
    predecessor_fee_cents: number | null;
  } | null;
}
export interface Summary {
  total: number;
  counts: Record<Verdict, number>;
  blockers: number;
  unresolved: number;
  /** Legacy case summary only; never use as a release verdict. */
  decision: string;
  scope: string;
}
export interface ReleaseVerdict {
  outcome: "PASS" | "FAIL" | "REVIEW" | "UNVERIFIED";
  reason: string;
}
export interface Run {
  correlation_id?: string;
  test_source?: string;
  lifecycle?: { state: string };
  metrics?: {
    duration_ms: number;
    sandbox_executions: number;
    model_calls: number;
  };
  release?: ReleaseVerdict | null;
  id: string;
  created_at: string;
  scenario: Scenario;
  execution_mode: string;
  execution_note: string;
  findings: Finding[];
  summary: Summary;
  policies: { policies: Policy[] };
  sources: { java: string; python: string };
  policy_sha256: string;
  source_sha256: { java: string; python: string };
  integrity_sha256: string;
  duplicates_removed: number;
  oracle_version: string;
}
export type RunHistoryItem = Pick<
  Run,
  "id" | "created_at" | "scenario" | "execution_mode" | "summary" | "release"
>;

// Presentation safeguard only: classification remains the backend's responsibility.
export function releaseVerdict(
  run: Pick<Run, "release" | "execution_mode">,
): ReleaseVerdict {
  const release = run.release;
  if (
    !release ||
    !["PASS", "FAIL", "REVIEW", "UNVERIFIED"].includes(release.outcome)
  )
    return {
      outcome: "REVIEW",
      reason:
        "Authoritative release verdict unavailable. Review the saved evidence.",
    };
  if (release.outcome === "PASS" && run.execution_mode !== "modal")
    return {
      outcome: "UNVERIFIED",
      reason: "Offline or unrecognized execution cannot verify a release PASS.",
    };
  return release;
}
export interface PolicySnapshot {
  id: string;
  created_at: string;
  policies: { policies: Policy[] };
}
export interface Generation {
  id: string;
  suite: {
    source: string;
    model: string | null;
    cases: TestCase[];
    analysis: string;
    rejected_count: number;
    duplicate_count: number;
    prompt_sha256: string | null;
  };
}
export interface BenchmarkRow {
  method: string;
  status: string;
  cases: number | null;
  detected: number | null;
  total_defects: number;
  detection_rate: number | null;
  false_alarms: number | null;
  elapsed_ms: number | null;
}
export interface Benchmark {
  status: string;
  seed?: number;
  rows?: BenchmarkRow[];
  limitations?: string[];
  defects?: { id: string; description: string; detected_by: string[] }[];
}
export const verdictLabels: Record<Verdict, string> = {
  compliant: "Compliant",
  unauthorized_regression: "Unauthorized regression",
  authorized_policy_change: "Authorized change",
  corrected_legacy_defect: "Legacy defect corrected",
  both_implementations_wrong: "Both implementations wrong",
  insufficient_policy_evidence: "Insufficient evidence",
  invalid_input: "Invalid input",
  execution_failure: "Execution failure",
};
export const money = (cents: number | null | undefined) =>
  cents == null
    ? "—"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(cents / 100);
