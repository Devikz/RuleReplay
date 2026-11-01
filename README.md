# RuleReplay

**Your code passed the tests. But did it follow the rules?**

RuleReplay compares a **legacy Java implementation**, an **updated Python implementation**, and an **independent deterministic oracle of approved financial policy**. It distinguishes regressions from authorized changes, corrected legacy defects, missing evidence, and execution failures.

Built by **Beyond Assertions** for the **Meta Global AI Developer Hackathon 2026**, theme **Push the Frontier**. All policies, fixtures, cases, and organizations in this project are fictional.

## What works now

- React/TypeScript/Vite/Tailwind workspace with generation, policy management, verification, detailed evidence, release summaries, JSON exports, and run history.
- FastAPI backend with validated versioned policy snapshots, integer-cent calculations, and eight deterministic classifications.
- Runnable local demo using explicitly labeled trusted fixture simulation; the checked-in Java and Python fixtures are also compiled/executed in tests.
- Real Meta Muse Wonder structured-generation client with credential/approval gates, strict validation, deduplication, and HTTP transport tests.
- Modal Sandbox adapter using the installed SDK's current filesystem API, bounded isolated execution, no injected credentials, blocked networking, and cleanup.
- Immutable local reports with source/policy hashes, independent evidence replay, and bounded counterexample shrinking.
- Reproducible ten-defect benchmark. Current local measurements: **3/10 conventional**, **6/10 seeded random**, **10/10 offline targeted boundary tests**. This is an **in-sample, known-defect benchmark with tuning**, not measured Muse Wonder performance or evidence of AI superiority.

**Live Meta and Modal execution have not been exercised.** They require your private credentials and explicit authorization for paid operations. No model weights, large datasets, or local container images are needed. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for test evidence and remaining gates.

## Local development

The environment has been set up in this checkout. Development servers use loopback only:

- Frontend: `http://127.0.0.1:5173`
- Backend/OpenAPI: `http://127.0.0.1:8000/docs`

For repeatable setup on another machine:

```sh
python3.12 scripts/setup.py
python3.12 scripts/dev.py
```

Prerequisites: Python 3.12, uv, Node.js 24/npm, and Java 17+ for trusted fixture tests. `scripts/setup.py` preserves an existing `.env`, installs locked dependencies, and checks secret exclusions. `scripts/dev.py` starts both servers and stops them together. Use `.venv/bin/python` or `uv run` for backend commands. One root virtual environment is sufficient for backend and developer tools.

Configuration comes from the project's root `.env` regardless of the working directory; process environment variables take precedence. Empty credentials allow offline startup. Invalid configuration errors reveal setting names, never values. `.env` is mode 0600, Git-ignored and untracked. `.env.example` documents the settings.

Meta defaults verified against official documentation on **2026-10-29**:

- Base URL: `https://api.meta.ai/v1`
- Model: `muse-wonder-1.0` (Muse Wonder, Standard mode)
- Endpoint: `POST /chat/completions` with `response_format.type = json_schema`.

[Meta models](https://dev.meta.ai/docs/models) · [Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions) · [Structured output](https://dev.meta.ai/docs/structured-output)

Only the account owner should insert credentials into `.env`, never into chat, frontend fields, or source. The two paid flags remain false. After explicit approval, `ALLOW_PAID_MODEL_REQUESTS=true` permits Meta calls and `ALLOW_BILLABLE_MODAL=true` permits Modal execution. Merely adding credentials does not enable either integration. Restart the backend after configuration changes. There is no UI endpoint that enables paid operations.

## Demo

1. Open **Verification** with **Payment-date policy bug** and **Trusted fixture simulator**.
2. Choose **Run current draft**. For due date **2026-10-30**, paid **2026-11-05**, Java charges **$25**; the buggy Python returns **$0**. The due date selects V1, whose five-day grace has expired: **unauthorized regression**.
3. Inspect the November 1 due-date case. V2's seven-day grace authorizes the updated $0 result even though legacy charges $25.
4. Select **Legacy threshold defect corrected** to see a corrected defect; inspect historical inputs to see insufficient evidence. Other scenarios demonstrate both implementations wrong and execution failure.
5. Open **Release summary**, replay the evidence, and export the JSON. The backend release verdict covers only tested cases; successful simulator runs remain **UNVERIFIED** in the workspace, history, summary and replay. Replay checks saved evidence consistency, not release approval.

The full three-minute narration is in [docs/DEMO.md](docs/DEMO.md).

## Checks

```sh
uv run ruff check .
uv run pytest --cov=rulereplay --cov-report=term-missing
npm --prefix frontend test
npm --prefix frontend run build
python3.12 scripts/check_secrets.py
uv run python -m rulereplay.benchmark
```

Tests disable outbound Python sockets and remove integration credentials from the test environment. All provider tests use mocks. The only host-executed Java/Python source is fixed, repository-owned test fixtures. Submitted or edited source is rejected in simulator mode and is routed exclusively to Modal after approval. CI runs the local checks with no provider secrets. CI has been authored but not run on GitHub because nothing has been pushed.

## Application contracts

- `GET /api/health`, `/api/policies`, `/api/fixtures`, `/api/fixtures/{scenario}`
- `POST /api/policy-sets`: validate and save a new immutable policy snapshot; `GET /api/policy-sets` lists snapshots.
- `POST /api/generate`: `mode` is `offline` or `meta`; returns a saved generation receipt.
- `POST /api/verify`: `mode` is `simulator` or `modal`; accepts a saved generation ID or up to 48 explicit case objects. Modal is capped at 16 cases / 32 sandboxes.
- `GET /api/runs`, `/api/runs/{id}`; `POST /api/runs/{id}/replay` recomputes the oracle and verdicts from saved observations, without executing code.
- `POST /api/runs/{id}/minimize/{case_id}`: shrink a trusted-simulation counterexample locally.
- `GET /api/benchmarks`: measured benchmark and explicitly unmeasured AI rows.

Inputs use ISO calendar dates (`YYYY-MM-DD`, years 2000–2100). The same strict date contract applies to policy effective dates and approval dates. A case has `id`, `due_date`, `payment_date`, and optional `rationale`. Unknown fields such as model-supplied expected fees are rejected. Source contract: Java class `LegacyLoan`, Python script, two date arguments, and one nonnegative integer fee in **cents** on stdout. Floating-point money, extra output, invalid input, and failed processes cannot silently pass.

Local records are in ignored `.local/reports/`. Source and policy snapshots are captured in each record; changing current policy does not rewrite historical evidence. The application is a single-user local prototype, not an authenticated public service.

## Project map

- `backend/rulereplay/`: API, domain validation, oracle, classifier, generator, execution, evidence and benchmark.
- `frontend/`: interactive React workspace.
- `data/`: synthetic approved policy evidence.
- `fixtures/`: original Java and Python demonstration implementations.
- `tests/`: unit, property, protocol, security and actual trusted cross-language checks.
- `benchmarks/`: measured results, input suites, counterexamples and [report](benchmarks/REPORT.md).
- `docs/`: [architecture](docs/ARCHITECTURE.md), [security](docs/SECURITY.md), [research](docs/RESEARCH.md), [demo](docs/DEMO.md), [attribution](docs/ATTRIBUTION.md).

## Limitations

Financial rules here are fictional flat late fees; no real regulations, holidays, time zones, interest accrual, partial payments, balances, or currency conversion are implied. Policy approvals are supplied provenance in a local demo, not authenticated organizational approvals. Content hashes detect accidental changes, not a malicious actor who can rewrite both data and hashes. The current suite deliberately exposes evidence gaps and the benchmark's in-sample leap-day tuning. Live provider behavior, Modal cold starts, costs, quotas, image builds, and network isolation require an approved live validation pass before submission claims can include them.

License: [MIT](LICENSE). Original implementation and AI-assisted contributions are documented in [docs/ATTRIBUTION.md](docs/ATTRIBUTION.md).

## Architecture and verification hardening

The original modular monolith and late-fee demo remain intact. New evidence controls include
immutable in-memory policy snapshots, nested fingerprint verification, complete-finding checks,
replay rationale checks, remote supervisor/child privilege separation, durable idempotency claims,
shared admission and conservative cloud-session budgets. No paid calls are enabled by this work.

Use `release.outcome` for the advisory state: **FAIL** for recorded policy violations, **REVIEW**
for missing/invalid evidence or execution failures, **UNVERIFIED** for simulator-only green runs,
and **PASS** only for tested compliant live observations. All are advisory and test-scoped; none
approve or deploy a release. Existing `summary.decision` remains as a compatibility field.

Live `/api/generate` and `/api/verify` require an `Idempotency-Key`; repeat exactly the same key
and request to recover a completed response. Uncertain accepted requests remain blocked for
operator review. The UI sends a new UUID per deliberate submission. One backend process is the
supported deployment; session budgets do not replace account-level cloud budgets.

Additional checks:

```sh
uv run bandit -r backend -q
uv run python scripts/security_audit.py
npm --prefix frontend run test:e2e
```

Browser tests use installed Chrome, two disposable loopback servers, temporary reports and
explicitly disabled paid settings. Dependency feed unavailability is reported separately from
vulnerabilities and never labeled a clean audit.

Engineering review documents:
[high-level design](docs/HIGH_LEVEL_DESIGN.md), [architecture review](docs/ARCHITECTURE_REVIEW.md),
[threat model](docs/THREAT_MODEL.md), [policy/classification model](docs/POLICY_MODEL.md),
[test strategy](docs/TEST_STRATEGY.md), [reliability](docs/RELIABILITY.md),
[evaluation](docs/EVALUATION.md), [operations](docs/OPERATIONS.md),
[architecture decisions](docs/adr/). Actual final checks are recorded in
[PROJECT_STATUS.md](PROJECT_STATUS.md).
