import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import App from "./App";

const counts = {
  unauthorized_regression: 1,
  compliant: 0,
  authorized_policy_change: 1,
  corrected_legacy_defect: 0,
  both_implementations_wrong: 0,
  insufficient_policy_evidence: 0,
  invalid_input: 0,
  execution_failure: 0,
};
const caseInput = {
  id: "transition",
  due_date: "2026-10-30",
  payment_date: "2026-11-05",
  rationale: "Cross transition",
};
const run = {
  id: "abc",
  created_at: "2026-10-29T12:00:00Z",
  scenario: "payment_date_bug",
  execution_mode: "simulator",
  execution_note: "Trusted fixture simulation; not a Modal execution.",
  release: { outcome: "FAIL", reason: "Policy violations detected." },
  sources: { java: "// saved Java", python: "# saved Python" },
  source_sha256: { java: "java-fingerprint", python: "python-fingerprint" },
  policy_sha256: "policy-fingerprint",
  findings: [
    {
      case_id: "transition",
      case: caseInput,
      verdict: "unauthorized_regression",
      reason: "Updated behavior violates approved policy.",
      legacy: { status: "ok", fee_cents: 2500 },
      updated: { status: "ok", fee_cents: 0 },
      oracle: {
        fee_cents: 2500,
        policy_id: "V1",
        days_late: 6,
        grace_days: 5,
        explanation: "Due date selects V1.",
      },
    },
    {
      case_id: "authorized",
      case: {
        ...caseInput,
        id: "authorized",
        due_date: "2026-11-01",
        payment_date: "2026-11-07",
      },
      verdict: "authorized_policy_change",
      reason: "Approved extension permits the changed result.",
      legacy: { status: "ok", fee_cents: 2500 },
      updated: { status: "ok", fee_cents: 0 },
      oracle: {
        fee_cents: 0,
        policy_id: "V2",
        days_late: 6,
        grace_days: 7,
        explanation: "Due date selects V2.",
      },
    },
  ],
  summary: {
    total: 2,
    blockers: 1,
    unresolved: 0,
    counts,
    decision: "hold",
    scope: "Supplied cases only.",
  },
  policies: { policies: [] },
  duplicates_removed: 0,
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      let data: unknown = {};
      if (url.endsWith("/health"))
        data = {
          status: "ok",
          integrations: {
            model: "muse-wonder-1.0",
            meta: { enabled: false, configured: false },
            modal: { enabled: false, configured: false },
          },
        };
      if (url.endsWith("/policies")) data = { policies: [] };
      if (url.endsWith("/policy-sets")) data = [];
      if (url.includes("/fixtures/"))
        data = { sources: { java: "// Java", python: "# Python" } };
      if (url.endsWith("/verify")) data = run;
      if (url.endsWith("/generate"))
        data = {
          id: "suite",
          suite: {
            source: "offline_boundary",
            analysis: "Deterministic boundaries.",
            cases: [caseInput],
            rejected_count: 0,
            duplicate_count: 0,
          },
        };
      if (url.endsWith("/replay"))
        data = { consistent: true, note: "No cloud call." };
      return { ok: true, json: async () => data };
    }),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function respondWith(overrides: Record<string, unknown>) {
  const original = vi.mocked(fetch).getMockImplementation()!;
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const value = overrides[String(input)];
    if (value !== undefined)
      return new Response(JSON.stringify(value), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    return original(input, init);
  });
}

const savedPolicy = {
  id: "SAVED-POLICY",
  name: "Saved approved rule",
  version: 3,
  status: "approved",
  effective_from: "2026-11-01",
  effective_until: null,
  grace_days: 9,
  fee_cents: 2500,
  provenance: {
    document: "SAVED-DOCUMENT §1",
    clause: "Saved approval extends grace to nine calendar days.",
    approved_by: "Fictional policy committee",
    approved_on: "2026-10-15",
    change_reason: "Synthetic saved snapshot",
  },
};

test("explains the product and locks unapproved paid execution", async () => {
  render(<App />);
  expect(
    screen.getByText(
      "Your code passed the tests. But did it follow the rules?",
    ),
  ).toBeInTheDocument();
  await screen.findByText("Local environment connected");
  expect(
    screen.getByRole("option", { name: /Modal Sandboxes/ }),
  ).toBeDisabled();
});

test("runs verification, inspects policy evidence and release decision", async () => {
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Local environment connected");
  await user.click(screen.getByRole("button", { name: "Run current draft" }));
  expect(
    await screen.findByRole("heading", { name: "Unauthorized regression" }),
  ).toBeInTheDocument();
  expect(screen.getByText("Due date selects V1.")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Release summary" }));
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  expect(screen.getByLabelText("Release advisory")).toHaveTextContent("FAIL");
  await user.click(
    screen.getByRole("button", { name: "Close release summary" }),
  );
  await user.click(
    screen.getByRole("button", { name: "Replay saved evidence" }),
  );
  expect(await screen.findByRole("status")).toHaveTextContent(
    "Evidence replay consistent",
  );
});

test("labels offline generation and creates a suite", async () => {
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Local environment connected");
  await user.click(screen.getByRole("button", { name: "Test generation" }));
  expect(
    screen.getByRole("option", { name: /Meta Muse Wonder/ }),
  ).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Generate hypotheses" }));
  expect(await screen.findByText("1 validated hypotheses")).toBeInTheDocument();
  expect(screen.getByText("offline boundary")).toBeInTheDocument();
});

test("edited code is blocked from local execution", async () => {
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Local environment connected");
  await user.click(
    screen.getByRole("button", { name: /implementation sources/ }),
  );
  await user.type(screen.getByLabelText("python source"), "print(0)");
  await user.click(screen.getByRole("button", { name: "Run current draft" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Edited source requires approved Modal",
  );
});

test("filtering findings keeps the evidence panel on a matching case", async () => {
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Local environment connected");
  await user.click(screen.getByRole("button", { name: "Run current draft" }));
  await screen.findByRole("heading", { name: "Unauthorized regression" });
  await user.selectOptions(
    screen.getByLabelText("Filter findings"),
    "authorized_policy_change",
  );
  expect(
    screen.getByRole("heading", { name: "Authorized change" }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("heading", { name: "Unauthorized regression" }),
  ).not.toBeInTheDocument();
  expect(screen.getByText("Due date selects V2.")).toBeInTheDocument();
  await user.selectOptions(
    screen.getByLabelText("Filter findings"),
    "execution_failure",
  );
  expect(
    screen.getByText("No findings match this filter."),
  ).toBeInTheDocument();
  expect(screen.queryByText("Due date selects V2.")).not.toBeInTheDocument();
});

test("historical reports show saved source and policy without replacing the current draft", async () => {
  const historic = {
    ...run,
    id: "historic",
    scenario: "corrected",
    execution_mode: "modal",
    execution_note: "Java and Python executed in separate Modal Sandboxes.",
    sources: {
      java: "// historical custom Java",
      python: "# historical custom Python",
    },
    policies: { policies: [savedPolicy] },
  };
  respondWith({ "/api/runs": [historic], "/api/runs/historic": historic });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Local environment connected");
  await user.click(
    screen.getByRole("button", { name: /implementation sources/ }),
  );
  await user.clear(screen.getByLabelText("python source"));
  await user.type(
    screen.getByLabelText("python source"),
    "# current draft Python",
  );
  await user.click(screen.getByRole("button", { name: "Run history" }));
  await user.click(
    await screen.findByRole("button", { name: "Open evidence" }),
  );
  const context = screen.getByRole("region", { name: "Saved run context" });
  expect(
    within(context).getByText(/Corrected update · Modal Sandboxes/),
  ).toBeInTheDocument();
  expect(
    within(context).getByText(
      /Java and Python executed in separate Modal Sandboxes/,
    ),
  ).toBeInTheDocument();
  await user.click(screen.getByText("Saved source and policy snapshot"));
  expect(screen.getByLabelText("Saved java source")).toHaveValue(
    "// historical custom Java",
  );
  expect(screen.getByLabelText("Saved python source")).toHaveValue(
    "# historical custom Python",
  );
  expect(screen.getByText(savedPolicy.provenance.clause)).toBeInTheDocument();
  expect(screen.getByLabelText("Scenario")).toHaveValue("payment_date_bug");
  expect(screen.getByLabelText("Execution")).toHaveValue("simulator");
  expect(screen.getByLabelText("python source")).toHaveValue(
    "# current draft Python",
  );
  await user.click(screen.getByRole("button", { name: "Run current draft" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Edited source requires approved Modal",
  );
});

test("saved policy snapshots can be selected after reload and reset to bundled policies", async () => {
  const snapshot = {
    id: "snapshot-123",
    created_at: "2026-10-29T12:00:00Z",
    policies: { policies: [savedPolicy] },
  };
  respondWith({ "/api/policy-sets": [snapshot] });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Local environment connected");
  await user.click(screen.getByRole("button", { name: "Policy library" }));
  await user.selectOptions(
    screen.getByLabelText("Policy snapshot for the current draft"),
    snapshot.id,
  );
  expect(
    screen.getByRole("heading", { name: savedPolicy.name }),
  ).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Test generation" }));
  await user.click(screen.getByRole("button", { name: "Generate hypotheses" }));
  await screen.findByText("1 validated hypotheses");
  const calls = vi.mocked(fetch).mock.calls;
  const request = calls.filter(([url]) => url === "/api/generate").at(-1);
  expect(JSON.parse(String(request?.[1]?.body)).policy_set_id).toBe(
    snapshot.id,
  );
  await user.click(screen.getByRole("button", { name: "Policy library" }));
  await user.selectOptions(
    screen.getByLabelText("Policy snapshot for the current draft"),
    "",
  );
  expect(
    screen.queryByRole("heading", { name: savedPolicy.name }),
  ).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Test generation" }));
  expect(
    screen.getByRole("heading", { name: "Your next test suite" }),
  ).toBeInTheDocument();
});

test("offline green run exposes unverified advisory and measured operations", async () => {
  respondWith({
    "/api/verify": {
      ...run,
      summary: {
        ...run.summary,
        decision: "pass",
        blockers: 0,
        counts: { ...counts, unauthorized_regression: 0, compliant: 1 },
      },
      findings: [{ ...run.findings[1], verdict: "compliant" }],
      release: {
        outcome: "UNVERIFIED",
        reason:
          "Simulator observations do not verify submitted implementations.",
      },
      test_source: "offline_boundary",
      lifecycle: { state: "NEEDS_REVIEW" },
      metrics: { duration_ms: 2, sandbox_executions: 0, model_calls: 0 },
      correlation_id: "correlation-123",
    },
  });
  render(<App />);
  await userEvent.click(
    await screen.findByRole("button", { name: /Run current draft/ }),
  );
  expect(
    await screen.findByLabelText("Verification advisory"),
  ).toHaveTextContent("UNVERIFIED");
  expect(screen.getByText(/0 sandbox executions/)).toBeInTheDocument();
  expect(screen.getByText("correlation-123")).toBeInTheDocument();
});

test.each(["PASS", "FAIL", "REVIEW", "UNVERIFIED"])(
  "%s is consistent across history, findings, details, summary and replay",
  async (outcome) => {
    // PASS here is a mocked API contract, never a measured live integration result.
    const saved = {
      ...run,
      execution_mode: outcome === "PASS" ? "modal" : "simulator",
      release: { outcome, reason: "Backend advisory for this saved run." },
      summary: { ...run.summary, decision: "pass" },
    };
    respondWith({ "/api/runs": [saved], "/api/runs/abc": saved });
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Local environment connected");
    await user.click(screen.getByRole("button", { name: "Run history" }));
    expect(
      await screen.findByLabelText("Historical release verdict"),
    ).toHaveTextContent(outcome);
    await user.click(screen.getByRole("button", { name: "Open evidence" }));
    expect(screen.getByLabelText("Verification advisory")).toHaveTextContent(
      outcome,
    );
    await user.click(screen.getByText("Saved source and policy snapshot"));
    expect(screen.getByLabelText("Saved python source")).toHaveValue(
      run.sources.python,
    );
    await user.click(screen.getByRole("button", { name: "Release summary" }));
    expect(screen.getByLabelText("Release advisory")).toHaveTextContent(
      outcome,
    );
    await user.click(screen.getByRole("button", { name: "Replay evidence" }));
    expect(
      await within(screen.getByRole("dialog")).findByRole("status"),
    ).toHaveTextContent(
      `Evidence replay consistent. Release verdict: ${outcome}.`,
    );
    expect(screen.getByLabelText("Release advisory")).toHaveTextContent(
      outcome,
    );
    expect(screen.queryByText("Hold release")).not.toBeInTheDocument();
  },
);

test.each(["simulator", "mock", "offline", "unknown"])(
  "%s execution cannot display a release PASS even with an inconsistent payload",
  async (execution_mode) => {
    const saved = {
      ...run,
      execution_mode,
      release: { outcome: "PASS", reason: "Untrusted passing label" },
      summary: { ...run.summary, decision: "pass" },
    };
    respondWith({ "/api/runs": [saved], "/api/runs/abc": saved });
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Local environment connected");
    await user.click(screen.getByRole("button", { name: "Run history" }));
    expect(
      await screen.findByLabelText("Historical release verdict"),
    ).toHaveTextContent("UNVERIFIED");
    await user.click(screen.getByRole("button", { name: "Open evidence" }));
    expect(screen.getByLabelText("Verification advisory")).toHaveTextContent(
      "UNVERIFIED",
    );
    await user.click(screen.getByRole("button", { name: "Release summary" }));
    expect(screen.getByLabelText("Release advisory")).toHaveTextContent(
      "UNVERIFIED",
    );
    expect(screen.queryByText("PASS", { exact: true })).not.toBeInTheDocument();
  },
);

test.each([undefined, null, { outcome: "pass", reason: "Legacy label" }])(
  "missing or invalid authoritative verdict requires REVIEW (%j)",
  async (release) => {
    const saved = {
      ...run,
      release,
      summary: { ...run.summary, decision: "pass" },
    };
    respondWith({ "/api/runs": [saved], "/api/runs/abc": saved });
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Local environment connected");
    await user.click(screen.getByRole("button", { name: "Run history" }));
    expect(
      await screen.findByLabelText("Historical release verdict"),
    ).toHaveTextContent("REVIEW");
    await user.click(screen.getByRole("button", { name: "Open evidence" }));
    expect(screen.getByLabelText("Verification advisory")).toHaveTextContent(
      "REVIEW",
    );
    await user.click(screen.getByRole("button", { name: "Release summary" }));
    expect(screen.getByLabelText("Release advisory")).toHaveTextContent(
      "REVIEW",
    );
    expect(screen.queryByText("PASS", { exact: true })).not.toBeInTheDocument();
  },
);

test("inconsistent replay shows an error without a successful replay claim", async () => {
  respondWith({ "/api/runs/abc/replay": { consistent: false } });
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText("Local environment connected");
  await user.click(screen.getByRole("button", { name: "Run current draft" }));
  await user.click(screen.getByRole("button", { name: "Release summary" }));
  await user.click(screen.getByRole("button", { name: "Replay evidence" }));
  expect(
    await within(screen.getByRole("dialog")).findByRole("alert"),
  ).toHaveTextContent("inconsistent evidence");
  expect(
    within(screen.getByRole("dialog")).queryByRole("status"),
  ).not.toBeInTheDocument();
});
