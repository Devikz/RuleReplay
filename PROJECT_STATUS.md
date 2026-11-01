# RuleReplay project status

Updated: 2026-11-01. Team: **Beyond Assertions**. Meta Global AI Developer Hackathon 2026.

**Offline readiness checkpoint: COMPLETE (2026-10-29).** Release presentation and demo
benchmark narration are corrected; the full offline validation and 98-path milestone
review are complete. Live Muse Wonder → Modal → Policy Oracle → Classification → Evidence
remains **UNVERIFIED; live integration readiness is NOT COMPLETE**. The final offline
checkpoint below supersedes the earlier REVIEW checkpoint without rewriting its history.

**Current preparation state (2026-11-01):** the 98-path milestone publication review and
staging/commit plan are ready for approval. The first bounded live smoke-test plan is prepared,
but no live attempt or dollar budget is approved. See the final section. Both paid gates remain off.

## Required implementation sequence

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Repository, secret files, instructions, Python 3.12 and frontend dependencies | Complete |
| 1 | FastAPI/React foundation, health, configuration, tests, CI | Complete |
| 2 | Approved policies, Java/Python fixtures, oracle, classification, boundary tests | Complete |
| 3 | Muse Wonder structured generation, validation, offline mode | Implemented; mock-tested, live call gated |
| 4 | Modal Sandboxes, bounded execution, errors, replay | Implemented; adapter tests, live execution gated |
| 5 | Verification workspace, generation, findings, evidence, release summary | Complete locally |
| 6 | 8–12 seeded defects and reproducible baseline comparisons | Local measurements complete; AI comparisons gated |
| 7 | Hardening, documentation, benchmark report, attribution, demo | Offline readiness complete; history advisory and demo narration corrected; live validation unverified |

## Confirmed setup evidence

- Initial repository: clean `main`, one initial commit, README/license/Python gitignore.
- Existing gitignore entries preserved; secret, frontend, cache, and build exclusions added.
- Root `.env` created with empty credentials, mode 0600; ignored and untracked.
- `.env.example` contains no credentials and is trackable.
- Python 3.12.16, uv, Node 24 and npm available. Root `.venv` created with Python 3.12.
- Official Meta docs checked 2026-10-29: `https://api.meta.ai/v1`, `muse-wonder-1.0`.
- Modal docs confirm network blocking, resource limits, sandbox lifetime and termination.

## Scope and constraints

The authoritative prompt was supplied in this chat. RuleReplay compares legacy Java,
updated Python, and approved policy. The synthetic late-fee scenario switches from a
five-day to seven-day grace period on **due dates** starting 2026-11-01. Fee: 2500 cents.
The deliberate updated-code bug chooses the policy by payment date.

No credentials have been requested or read into output. No paid API request, Modal
resource, Git commit, push, or publication has been made. Live integrations remain
blocked until credentials are supplied privately and paid operations are approved.

## Phase 1 verification

Python dependencies installed and locked with uv; frontend dependencies installed and locked with npm. Backend: 7 tests pass. Frontend: 1 test passes. Production build and Ruff pass. Secret checks pass. No provider requests were made.

## Phase 2 verification

33 backend tests passed, including actual Java compilation/execution and Python execution of fixed repository-owned fixtures for four scenarios. Oracle remains independent. Hypothesis checks fee monotonicity. No submitted source was executed locally.

## Integration validation

Phase 3: 41 backend tests passed. Official structured-output protocol implemented with HTTPX, schema validation, deduplication, bounded responses and no automatic paid retries. No live AI results claimed. Phase 4 uses Modal 1.6.3 filesystem API (not removed legacy `Sandbox.open`), fresh sandbox per implementation/case, no credentials inside execution, and offline evidence replay. Live provider validation remains blocked on credentials and explicit paid-operation approval.

## Phase 5 verification

55 backend tests and 4 frontend interaction tests passed. Production build passed. Browser-tested actual local API: default run (16 cases, 1 regression, 3 authorized changes, 4 evidence gaps), release summary, evidence replay, and offline generation. Meta and Modal controls visibly disabled. Responsive narrow layout inspected.

## Final local verification (2026-10-29)

- **106 backend tests pass; 90% statement coverage.** Oracle and classifier: 100% statement coverage. This includes mocked sandbox harness resource/timeout/output tests, not live sandbox validation.
- **7 frontend interaction tests pass**, covering paid gates, local verification/evidence/release/replay, offline generation, rejection of edited source, saved report context, filtered evidence, and saved policy snapshot selection.
- TypeScript and production build pass; frontend bundle is approximately 280 KB uncompressed. Ruff and Prettier checks pass.
- Secret scanner and Git whitespace checks pass. `.env` remains ignored, untracked, mode 0600. Loading settings from outside the repository resolves the root dotenv correctly. Both paid flags remain false.
- Repeatable `scripts/setup.py` completed using frozen Python and npm lockfiles without changing secret settings.
- Browser verified local run, evidence replay, release summary and offline generation; narrow responsive layout inspected.
- Ten seeded defects measured with 48 cases per method: conventional 3/10; seeded random 6/10; offline RuleReplay boundaries 9/10. D10 (leap-day omission) survived the measured suites. Checked-in suites and scores are verified by an automated consistency test.
- Meta-without-policy and full Muse Wonder benchmark rows are **unmeasured**, not zero-score measurements. No claim of AI superiority is made.
- Dependency storage: roughly 91 MB Python environment, 108 MB uv cache, 180 MB frontend dependencies before small formatting-tool additions. No weights, datasets, Docker images, or cloud resources downloaded/created.
- Current FastAPI/Starlette emits a non-failing TestClient deprecation notice about HTTPX; protocol and integration tests pass. The optional macOS fsevents install-script notice does not prevent setup or Vite execution.

## Delivered documentation

README, architecture/classification contracts, security review, primary research references,
measured benchmark report/data, hackathon contribution attribution and a three-minute demo script.
The local app is available at http://127.0.0.1:5173 while its development servers are running.

## Remaining user-dependent work

1. User privately supplies MODEL_API_KEY, MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in the already-created `.env` when ready.
2. User explicitly approves a bounded live-test budget before enabling paid flags. Then validate actual Muse Wonder generation, Modal image build/execution/egress blocking/timeouts/cleanup, and record the two AI benchmark ablations.
3. Final demo recording and hackathon submission. Any GitHub push/publication needs separate approval. No commit or push has been made.

Execution-feedback-guided iterative AI generation is deferred; bounded counterexample minimization, mutation evaluation and metamorphic testing are implemented. This project is a working local prototype with gated, mock-tested cloud adapters, not a claim of completed live cloud validation.

## Continuation audit and fixes (2026-10-29)

- Strict YYYY-MM-DD dates now apply to test inputs, policy effective periods and approval provenance. Numeric timestamps, ISO week dates and out-of-range years are rejected; custom policy dates can no longer overflow offline generation. Blank approval evidence is rejected.
- Malformed Meta completion envelopes return sanitized generation errors instead of uncaught attribute errors; all tests use mocked HTTP transport.
- The remote harness rejects stdout over its byte limit rather than accepting a valid truncated prefix. Modal's actual timeout exception hierarchy and timeout return-code sentinel are mapped to `timeout`, with cleanup verified by mocks.
- Malformed evidence JSON objects/checksum shapes fail with safe RecordError messages. Invalid-input finding IDs use a reserved separator to avoid collisions with valid user case IDs.
- Saved reports now have a labeled immutable context and a read-only inspector for their actual source text, policies and fingerprints. The current draft remains separate and its execution button is explicit. Existing policy snapshots can be selected after reload or reset to bundled policies.
- Finding filters update the selected evidence and clear it when empty. Regression headlines state the deterministic verdict without asserting an unproven root cause.
- All five offline scenarios were exercised through FastAPI and successfully replayed. Backend: 106 tests, 90% statement coverage; oracle/classifier remain at 100%. Frontend: 7 interaction tests, production build and formatting checks pass. Ruff and secret/Git whitespace checks pass. Benchmark consistency tests retain measured 3/10, 6/10 and 9/10 results, with both live AI rows unmeasured.
- Browser smoke checks confirm the current-draft run, filter/evidence synchronization, clearing of stale evidence, policy snapshot save/reload/reselection/reset, opening a historical report, and the release summary. Local servers were restarted to load the fixes. No paid flags, credentials, Git commits or remote repository state were changed.

## Senior hardening Phase A — actual baseline (2026-10-29)

Read the application, tests, integration adapters, evidence/replay, frontend, dependencies
and CI. Reproduced **106 backend tests / 90% coverage**, **7 frontend tests**, build,
Ruff, Prettier, secret scan and Git whitespace checks. The sandbox's default uv cache
was inaccessible; `UV_CACHE_DIR=/private/tmp/rulereplay-uv-cache` resolves it without
changing project dependencies. Findings and priorities: `docs/ARCHITECTURE_REVIEW.md`.
No user files discarded, no credentials changed, no paid calls, commits or pushes.

## Senior hardening Phases B–E — implementation and regression evidence

- **B:** The Modal supervisor now stays privileged only inside the remote sandbox and
  drops child supplementary groups/GID/UID to 65534. No host source execution was added.
  Provider error text is normalized, nonfinite timings rejected, generated-input rejection
  reasons and bounded token metadata captured. Mocked adversarial tests cover policy/source
  injection, extra command/verdict fields, malformed and oversized responses and UID order.
- **C:** Policies/provenance are deeply immutable after validation. Canonical hashing no
  longer depends on generation. Saved reads and replay validate nested source/policy/generation
  fingerprints and complete findings; replay compares reasons as well as verdicts/oracle.
  Fixed zero-fee grace explanation. Added PASS/FAIL/REVIEW/UNVERIFIED advisory with simulation
  unable to produce PASS. Original summary fields retained for compatibility.
- **D:** Added 300 deterministic Hypothesis money/date/threshold examples and 150 interval/gap
  examples, metamorphic identity/repeatability checks, AST dependency boundaries, and negative
  evidence tests. Original 106 tests preserved. Intermediate full result: **151 backend tests,
  92% statement coverage; eight frontend tests and production build pass**.
- **E:** Shared nonblocking admission, session model/sandbox budgets, durable idempotency claims,
  validated lifecycle and safe structured events/errors. Atomic evidence persistence precedes
  publishing terminal success. Concurrent requests, restart deduplication, failed claims,
  storage failure, budget exhaustion and transition tests pass. Single-process limitation is
  explicit; interrupted accepted cloud operations are never retried automatically.
- Offline benchmark rerun: **3/10 conventional, 6/10 seeded random, 10/10 offline boundaries**.
  The last improvement deliberately targets the previously observed leap-day survivor;
  documented as in-sample tuning. Live AI methods remain unmeasured.
- Python and npm online vulnerability audits completed with **zero reported findings**.
  Small audit tools and Playwright package added; existing Chrome reused, no browser download.
  Browser-test initial launch hit sandbox loopback permissions; rerun with authorized local
  process access underway. Final results below will supersede intermediate counts.

## Senior hardening Phase F — supply chain and CI

Added locked Bandit and pip-audit developer tools, npm audit integration with explicit
UNAVAILABLE versus FINDINGS status, common credential-pattern scanning, and audit-result
classification regressions. Both live vulnerability feeds returned **zero reported findings**;
Bandit completed with **zero unsuppressed findings and zero scan errors**. Remote-only subprocess
and sandbox paths have specific documented suppressions; no global security rule was disabled.
Actions use verified commit SHAs, read-only permissions, no persisted checkout credentials,
Ubuntu 24.04, a 15-minute job limit, locked installs and no provider credentials. Dependabot
configuration covers uv, npm and Actions. Actual GitHub-hosted CI remains unrun (no push authorized).

## Senior hardening Phase G — observability and documentation

Completed HIGH_LEVEL_DESIGN, ARCHITECTURE_REVIEW, THREAT_MODEL, TEST_STRATEGY, RELIABILITY,
POLICY_MODEL, EVALUATION, OPERATIONS, SECURITY updates and seven ADRs. Six required Mermaid
architecture diagrams were rendered successfully using installed Chrome and a temporary parser.
Added stage/correlation traces, separate validation/execution/evaluation duration metrics,
storage-latency events, model usage/template metadata, rejection reasons, sandbox counts,
classifier version and replay runtime-context differences. UI displays the backend advisory,
run/correlation IDs, test source and operation counts. Replay feedback now appears inside the
open release dialog, including failure messages. Exact source changes: docs/HARDENING_CHANGELOG.md.

## Senior hardening Phase H — final measured validation (2026-10-29)

- **162 backend tests pass; 92.24% statement coverage** (90% minimum gate passes).
  Oracle and classifier remain at **100% statement coverage**. All original tests retained.
- **8 frontend tests pass**; TypeScript/Vite production build and Prettier checks pass.
- **1 real Chrome end-to-end test passes** against disposable offline FastAPI/Vite servers:
  scenario selection, findings, actual policy clause, release advisory, saved-evidence replay,
  offline generation and execution-failure REVIEW. No model/cloud calls or browser downloads.
- New property tests run up to **450 reproducible Hypothesis examples** across dates, fee amounts,
  grace periods and policy intervals/gaps, in addition to original properties. Adversarial,
  malformed-evidence, injection, privilege-boundary, failure, idempotency and architecture tests pass.
- Ruff, Bandit, secret scan and Git whitespace checks pass. Python/npm dependency feeds both
  returned zero reported vulnerabilities. Coverage XML and audit details are local ignored outputs.
- Final benchmark: conventional **3/10** (48 supported), random **6/10** (48 supported), offline
  boundaries **10/10** (39 supported out of 48). Zero control false alarms; authorized-change
  checks 0/2/6 respectively with zero false positives. Boundary targets covered 0/12, 2/12,
  12/12. Saved simulator evidence replay is consistent for all three. Actual timings are in JSON.
- The 10/10 offline result is **in-sample tuning against the known D10 survivor**. Both live
  AI rows remain unmeasured; tokens/costs are null unless actually returned in a live receipt.
- Python environment approximately **107 MB**, frontend dependencies **215 MB**. The temporary
  Mermaid validation dependencies are removed after validation; no model weights or Docker images.
- Actual root settings checked without printing secrets: **both paid flags false**, `.env` mode
  **0600**, ignored and untracked. No `.env` values changed, no commits, pushes or publication.

### Remaining limitations and approvals

This is a local single-user/single-process prototype. Policy provenance is user asserted;
file hashes are not signatures. Session budgets reset on restart. Report and idempotency receipt
writes have a documented recovery window. Total retention quotas, authenticated multi-user
access, provider-wide spending enforcement and absolute control-plane deadlines are not implemented.
HTTPX TestClient deprecation and Node color-environment notices are non-failing tool warnings.

Real Muse Wonder quality/latency/token-cost behavior and Modal egress, UID isolation, cold starts,
OOM/timeouts/cleanup remain **unverified**. They require private credentials plus explicit approval
of a bounded live test budget. No further approval is needed for the completed local hardening.
Any commit, push, publication or live paid test still requires separate explicit approval.

## Release-readiness checkpoint — 2026-10-29

Historical checkpoint, superseded by the final offline readiness checkpoint below.

**Decision: REVIEW.** The hardened local prototype runs and its existing suites pass.
It is not ready for an unqualified release-readiness claim: a remaining history UI issue
can misleadingly display “pass” for simulated execution. No application code, features,
tests, demo script or benchmark data were changed during this checkpoint. Only this
status document was edited; ignored diagnostic outputs were regenerated.

### Checks rerun and actual evidence

Python commands used `UV_CACHE_DIR=/private/tmp/rulereplay-uv-cache`; the backend test
command also explicitly set both paid flags false. Existing tests remove credentials
and block outbound sockets; browser tests use temporary reports and disabled providers.

| Check | Current result |
| --- | --- |
| `uv run pytest --cov=rulereplay --cov-report=term-missing --cov-report=xml --cov-fail-under=90` | 162 passed; 92.24% statement coverage; oracle/classifier 100% |
| `uv run ruff check .` | Passed |
| `uv run bandit -r backend -q` | Exit 0, no unsuppressed findings; redundant `nosec` warnings remain |
| `npm --prefix frontend test` | 8 passed |
| `npm --prefix frontend run build` | TypeScript and Vite passed |
| `npm --prefix frontend run format:check` | Passed |
| `npm --prefix frontend run test:e2e` | 1 installed-Chrome test passed against disposable offline FastAPI/Vite servers |
| `uv run python scripts/security_audit.py` | Python PASS, npm PASS; zero reported findings from both feeds on the network-enabled rerun |
| `uv run python scripts/check_secrets.py` | Passed, including built frontend bundle |
| `git diff --check` and `git diff --cached --check` | Passed |

The first restricted browser run could not bind loopback (EPERM). The first restricted
dependency audit returned UNAVAILABLE for both feeds, correctly classified as UNVERIFIED.
Permission-reviewed reruns succeeded; unavailable results were not counted as clean audits.
HTTPX TestClient deprecation and Node color-environment warnings remain non-failing.
GitHub-hosted CI has not run, and neither successful mocks nor local Chrome establish live
provider behavior. Dependency findings are point-in-time feed results, not a security guarantee.

Additional disposable, socket-blocked FastAPI smoke checks exercised all five scenarios
with 16 cases each and consistent evidence replay: payment-date bug FAIL, corrected REVIEW,
legacy defect REVIEW, both-wrong FAIL, execution error REVIEW. The corrected/legacy-defect
suites retain policy-coverage gaps. Offline generation produced 16 cases, linked its saved
receipt to verification, and replayed consistently. No submitted source ran on the host.

### Manifest and commit boundary

`docs/HARDENING_CHANGELOG.md` contains **67 unique paths**. All exist and all belong to
the current changed/untracked set; there are no missing, duplicate or unchanged entries.
It is a pass-specific inventory, **not the entire working-tree manifest**. Relative to
HEAD `14c7284` (Initial commit), there are **98 changed/untracked files: 2 modified tracked
files and 96 untracked files**. Nothing is staged. Git tracks only `.gitignore`, `README.md`
and the unchanged `LICENSE` (99 total publishable working-tree files).

The other 31 paths are:

```text
.npmrc
.python-version
backend/rulereplay/__init__.py
backend/rulereplay/fixtures.py
backend/rulereplay/minimize.py
backend/rulereplay/policies.py
backend/rulereplay/simulator.py
data/policies.json
docs/ATTRIBUTION.md
docs/DEMO.md
docs/RESEARCH.md
fixtures/legacy/LegacyLoan.java
fixtures/updated/corrected.py
fixtures/updated/loan.py
frontend/index.html
frontend/src/main.tsx
frontend/src/styles.css
frontend/src/test-setup.ts
frontend/src/vite-env.d.ts
frontend/tsconfig.json
scripts/dev.py
scripts/setup.py
tests/conftest.py
tests/test_api.py
tests/test_benchmark.py
tests/test_config.py
tests/test_engine.py
tests/test_evidence.py
tests/test_generation.py
tests/test_sandbox_harness.py
tests/test_trusted_fixtures.py
```

There is no committed pre-hardening application baseline or content-hash manifest to
prove the historical 67-file attribution byte for byte. The path inventory is reconciled;
the historical diff remains unverified. A runnable first milestone needs the full reviewed
98-file set, including its earlier prototype dependencies, rather than only the 67 paths.

### Secret and artifact boundary

The existing scanner passed, followed by separate checks of all 99 publishable working-tree
files, all three index blobs and all three HEAD blobs against known private dotenv values
and common credential/private-key patterns. No matches or publishable symlinks were found.
No private values were printed. This is a bounded scan, not proof against every unknown
secret format; synthetic credential strings in tests are deliberate mock data.

`.env` exists with mode **0600**, is ignored and is neither tracked nor staged. No dotenv
values were changed. Both paid flags are **false**; the configured Meta key, Modal token ID
and Modal token secret are all absent (presence only inspected). `.env.example` has empty
credential fields. `.local/` reports/security artifacts, frontend build/browser outputs and
coverage outputs are ignored and absent from the index. No sensitive artifacts are staged.

### Release-verdict review and remaining local blockers

- `verification.release_outcome` gives recorded regressions/both-wrong findings FAIL;
  absent/invalid evidence, rejected generation inputs and execution failures require REVIEW
  when no conclusive defect takes precedence. Otherwise simulator mode gives UNVERIFIED.
  PASS requires Modal mode with acceptable findings. `automatic_approval` is always false.
  Oracle/classifier dependency tests and evidence/replay regressions passed. Failed or
  truncated model completions are rejected before a suite is accepted.
- **Release presentation blocker:** a one-case simulator run for due/payment 2026-11-01
  produces `release.outcome=UNVERIFIED`, `lifecycle.state=NEEDS_REVIEW`, but legacy
  `summary.decision=pass`. `GET /api/runs` (`backend/rulereplay/api.py`, runs handler)
  omits `release`, and `frontend/src/App.tsx` renders that legacy value under “Release
  decision” in history. Reproduced through the real local API and confirmed in rendering
  code. The workspace/dialog use the advisory correctly; the app-wide no-misleading-PASS
  requirement is therefore **not satisfied**. Correct the history API/UI and add focused
  API/UI regression coverage before calling hardening complete.
- **Demo narration blocker:** `docs/DEMO.md` still says offline boundaries detect 9/10 and
  the leap-day defect survives. Current saved benchmark and consistency tests establish
  10/10 with deliberate in-sample D10 tuning. Update the narration to disclose that tuning
  before recording/presenting the scripted benchmark segment. Scores were not edited or
  regenerated because the generator/source did not change in this checkpoint.
- Offline *generation* may legitimately feed real Modal execution; it does not establish
  Muse Wonder participation. A scoped PASS would describe those executed cases only.
  The existing injected-gateway PASS test is a mock, not live evidence. Mode labels and
  local hashes are not provider attestations or digital signatures; replay recomputes
  classifications from saved observations, without re-executing code.

### Blockers and bounded plan for one real end-to-end test

No real chain has been executed. Required before proceeding:

1. Privately supply credentials and confirm account access to Muse Wonder and Modal.
   Credentials are currently absent; paid flags remain disabled.
2. Obtain explicit approval for model-call count, sandbox count, image/app provisioning
   and a maximum dollar spend. Suggested first scope: **one model request for four cases,
   at most eight sandboxes** (Java/Python per case), one backend process, no automatic
   retries. This scope is a proposal, not permission or a cost estimate. Account-level
   spend controls are needed because session counters reset and do not enforce dollars.
3. Resolve the history advisory and demo narration issues. For the live test, retain the
   exact policy/source snapshots, validate the generated receipt and accepted case count,
   and inspect any rejected/unsupported cases before launching execution. Link verification
   by `generation_id`; do not substitute an offline suite and call it Muse Wonder evidence.
4. After approval only, record the actual generation → Modal observations → oracle →
   classification → persisted report → consistent replay chain. A valid FAIL exposing the
   seeded regression is a successful pipeline test, not a reason to manufacture PASS.
   Capture actual provider/resource identifiers and usage privately, verify cleanup, and
   disable paid gates afterward. An interrupted ACCEPTED claim requires provider/evidence
   inspection before another billable attempt.

Actual structured-output compatibility, model quality/latency/token cost, image provisioning,
Java/Python execution and cleanup remain unverified. Modal egress blocking, UID isolation,
OOM, timeout, output-limit and descendant-process behavior need separately scoped live
checks; one happy-path chain cannot certify them. AI benchmark ablations and GitHub CI
also remain unmeasured/unrun. No deployment or production-readiness claim is warranted.

### Proposed milestone commit (not created)

Summary: establish the Java/Python/policy-oracle verification prototype with isolated,
paid-gated adapters; immutable evidence/replay; evidence-derived advisories; durable
operation claims and budgets; architecture/security/property/browser tests; and disclosed
synthetic benchmarks and operations documentation. Include this checkpoint's open issues
and explicit live-validation limits. Review all 98 paths before staging/commit approval.

Recommended message:

```text
feat: establish policy-backed verification with architecture hardening
```

Safest next action: correct the two local release-presentation/documentation issues with
focused regression tests for the code fix, then review the full milestone and request
explicit commit approval. Keep paid gates off. A bounded live test and any push require
separate approval. **No commit, staging, push, paid API call, deployment or publication
was performed during this checkpoint.**

## Final offline readiness checkpoint — 2026-10-29

**Decision: OFFLINE READINESS COMPLETE. Live integration readiness: UNVERIFIED / NOT COMPLETE.**
The two previously identified offline blockers are resolved. This checkpoint authorizes no
paid calls, Git operations or deployment; adding credentials does not itself authorize billing.

### Fixes and release-label regression evidence

- History now returns the saved backend `release` advisory. It preserves the compatibility
  `summary.decision` without using it as a release verdict. Backend classification, precedence,
  evidence hashes and replay semantics are unchanged.
- A shared typed presentation renders PASS, FAIL, REVIEW or UNVERIFIED in history, the saved
  workspace/findings/evidence context and release summary. Replay reports evidence consistency
  and repeats the same verdict, explicitly without code re-execution or release approval.
- Missing/null/invalid historical advisories display REVIEW; PASS with simulator, mock, offline
  or unknown execution displays UNVERIFIED. Only the PASS badge is green. The ambiguous
  “Cases verified” metric now says “Cases evaluated”; case compliance is separate from release
  approval. No production frontend rendering reads `summary.decision`.
- **6 added API regression cases pass:** all four advisory values plus legacy missing advisory,
  and an actual successful simulator run retaining UNVERIFIED in history/details/after replay.
- **12 added frontend regression cases pass:** four verdicts across history/findings/details/
  summary/replay; four non-Modal PASS guards; three missing/invalid advisory cases; one replay
  mismatch. The existing offline-success test now uses a passing legacy summary and green case.
  All original eight UI tests remain. Mocked PASS payloads prove presentation contracts only;
  mode labels/hashes are not provider attestations, and no live PASS is claimed.
- The new real Chrome test creates a compliant simulator case through the actual local API,
  confirms legacy `summary.decision=pass` alongside `release.outcome=UNVERIFIED`, and verifies
  that history, details, summary and consistent replay never promote it to release PASS.
- DEMO and README now state the freshly rerun benchmark values and in-sample known-defect
  tuning. The benchmark UI also makes the tuning and absence of Muse Wonder evidence explicit.

### Exact final validation

Commands below used `UV_CACHE_DIR=/private/tmp/rulereplay-uv-cache` for uv where needed.
Python is 3.12.16; Chrome was already installed. No dependency/browser/model download was needed.

| Check | Result |
| --- | --- |
| `uv run pytest --cov=rulereplay --cov-report=term-missing --cov-report=xml --cov-fail-under=90` | **168 passed**, 1 non-failing HTTPX/Starlette deprecation warning; **92.24%** statement coverage (1,130/1,225 statements); oracle and classifier **100%** |
| `npm --prefix frontend test` | **20 passed**, including all release-label regression cases |
| `npm --prefix frontend run build` | TypeScript and Vite production build pass; JS 263.24 kB / 81.26 kB gzip; CSS 25.69 kB / 7.01 kB gzip |
| `uv run ruff check .` | Pass |
| `uv run ruff format --check .` | Pass; 72 Python files formatted |
| `npm --prefix frontend run format:check` | Pass; now includes browser tests and Playwright config alongside app source/Vite config |
| `uv run python scripts/check_secrets.py` | Pass for publishable source and built browser assets; no known local credentials or configured credential-pattern findings |
| `uv run bandit -r backend -q` | Pass; zero unsuppressed findings; non-failing warnings for existing narrowly scoped suppressions |
| `uv run python scripts/security_audit.py` | Python **PASS, 0 findings**; npm **PASS, 0 findings** from public vulnerability feeds |
| `npm --prefix frontend run test:e2e` | **2 passed** in installed real Chrome, disposable offline API/Vite servers; no dotenv, model calls or Modal execution |
| `uv run python -m rulereplay.benchmark` | Recomputed report/JSON: conventional **3/10**, seeded random **6/10**, offline targeted boundary tests **10/10** |
| Lockfiles / publication checks | `uv lock --check --offline`, `npm ls --depth=0`, secret scan, local documentation links, full-file whitespace/conflict checks and `git diff --check` pass |

The initial restricted-environment dependency audit returned UNAVAILABLE for both feeds;
that was not counted as a clean result. A network-enabled rerun produced the PASS results
above. Chrome initially could not bind loopback inside the restricted sandbox; the local
process-enabled rerun exposed an ambiguous locator in the new test. Narrowing that locator
resolved it; both browser tests passed afterward. A TypeScript error in the new test options
and formatting differences were corrected before the final passing build/checks. No application
regression remained. Non-failing Node color-environment notices also remain.

### Measured benchmark and scope

Each measured method uses 48 cases: conventional 48 supported, random 48 supported, offline
targeted boundaries 39 supported. Detection is **3/10, 6/10 and 10/10**, respectively; all three
have zero correct-control false alarms and consistent saved simulator replay. The deterministic
offline generator was previously tuned against the known D10 leap-day survivor. This remains
an **in-sample, known-defect benchmark with tuning**, not independently held-out evidence.
Both AI rows are unmeasured; no Muse Wonder 10/10 or AI superiority claim is made. The earlier
9/10 entries above describe historical measurements and are not the current score.

### Milestone, secrets and Git

The complete inventory is reconciled in [HARDENING_CHANGELOG.md](docs/HARDENING_CHANGELOG.md):
**67 hardening paths + 31 additional milestone paths = 98 changed/untracked paths**. The
unchanged LICENSE makes 99 total publishable paths. Source, original and new tests, synthetic
fixtures/policies, configuration, scripts, lockfiles and documentation are present. Benchmark
report/JSON and dependency locks are intentional reproducibility artifacts; local reports,
audit/coverage/build/browser outputs, environments and dependency directories remain ignored.

Root `.env` is **ignored, untracked, nonsymlinked, mode 0600**, with all three provider credentials
absent and both paid flags **false**. Its values were not changed or printed. `.env.example` is
trackable with empty credentials. The publication review found no secrets, customer data,
vendored dependencies, credential-bearing lockfile URLs, binaries, symlinks, conflict markers
or trailing whitespace. Lockfile download hosts are public PyPI/Python package hosting and npm.

Git remains on `main` with one existing commit, **2 modified tracked files and 96 untracked
files**, no staged changes, deletions or merge conflicts. `git fsck --no-reflogs` found two
dangling trees and no corruption; nothing was pruned. Only README, LICENSE and `.gitignore`
are currently tracked, so a future approved milestone commit must include the full inventory.
No commits, author dates, historical contributions or historical benchmark scores were invented
or backdated. No staging, commit, push, publication, deployment or paid API call occurred.

### Remaining live integration blockers

Private credentials/account access and explicit approval of a bounded model/sandbox/dollar
budget are still required before enabling either paid gate. Actual Muse Wonder structured
generation, quality, latency and usage/cost; Modal provisioning, Java/Python execution, egress
denial, UID isolation, timeout/OOM/output/descendant handling and cleanup; the complete persisted
live chain/replay; and independently evaluated live AI benchmark ablations remain unverified.
GitHub-hosted CI, public publication and final recorded demo also remain outstanding. Maintain
one backend process and inspect any ACCEPTED durable claim before risking repeat billing.

## Safeguarding and live-validation preparation — 2026-11-01

**Offline readiness remains COMPLETE. Live integration readiness remains UNVERIFIED.**
Only planning documentation was changed in this preparation; the core product and its tests
were not modified. The October 29 full-suite results remain historical evidence, not tests
rerun on November 1.

### Fresh review and configuration evidence

- Reconciled all **98 changed/untracked files** against the existing manifest: 67 hardening
  files plus 31 broader milestone files. All belong in source control. The unchanged tracked
  LICENSE makes 99 publishable paths. Reviewed path/content structure, license notices,
  dependency and measured-data artifacts, sensitive-data patterns and publication exclusions.
- Secret scan passes for publishable files and the built browser bundle. The full set has no
  binaries, symlinks, conflict markers, trailing whitespace, oversized file or accidentally
  included environment/dependency/cache directory. Largest files are `uv.lock` (146,440 bytes)
  and frontend lockfile (104,064 bytes); both are required reproducibility artifacts.
  The 77 Python package and 190 npm dependency entries have public-registry URLs without
  embedded credentials. Synthetic policy/fixture/test/benchmark data contains no customer dataset.
- Keep the benchmark Markdown/JSON, lockfiles and all source/tests/documentation. Exclude `.env`,
  `.local/` receipts/reports/audits/review diagnostics, `.venv/`, frontend dependencies/builds,
  uv/bytecode/test caches, coverage and browser output. Current local footprints: approximately
  107 MB Python environment, 215 MB frontend dependencies, 108 MB uv cache, 292 KB browser build;
  these are all ignored. No model weights, Docker images or vendored packages were added.
- Existing MIT license matches HEAD byte-for-byte with its original notice. Source notice
  review found no conflicting proprietary block or inappropriate new license assertion.
  Attribution and dependency license metadata remain intact. No authorship/date history was
  invented. Future packaged redistribution may need a separate dependency-license review.
- Root `.env` is **ignored, untracked, nonsymlinked, mode 0600** and unchanged, verified by
  before/after byte fingerprints. `.env.example` is trackable; the three secret assignments
  are empty and all other values are public configuration/defaults. No secret value was printed.
- Actual `load_settings()` from outside the repository resolves root dotenv correctly.
  Current Meta and Modal health states both show **enabled=false, configured=false**; the
  three provider credentials are absent. Both paid gates reject locally before provider access.
- A temporary synthetic dotenv proved all three credential variables and the proposed
  1-model/4-case/8-sandbox limits load, without changing root `.env`. Health exposed no test
  credential text. The preflight blocked outbound Python sockets; no provider SDK connection,
  credential validation, model inference or cloud provisioning occurred.
- Focused configuration/API/execution/reliability suites: **43 passed** on 2026-11-01, with one
  non-failing existing HTTPX/Starlette deprecation warning. `git diff --check`, full-file
  whitespace/conflict/manifest checks and the secret scanner pass. No need to repeat the
  complete UI/browser/coverage suites for planning-only edits; their exact October 29 results
  remain recorded above. No new vulnerability-feed scan was claimed for this preparation.

### Prepared milestone staging/commit

The complete path allowlist, group counts, exclusions and post-approval execution sequence
are in [HARDENING_CHANGELOG.md](docs/HARDENING_CHANGELOG.md). Stage only its 98 explicit paths,
inspect/scan the exact staged bytes and confirm the path set before creating a local commit.
Current Git state remains `main`, one existing commit, **2 modified tracked files + 96 untracked
files**, empty index and no merge conflicts. Two dangling trees remain without corruption or
pruning. Until the milestone is committed, most of the application is still untracked.

Recommended milestone commit message:

```text
feat: establish policy-backed RuleReplay verification platform
```

Use the actual commit date and existing Git identity; do not fabricate historical contributions.
No staging, commit, push, history rewrite or publication has occurred. Explicit staging/commit
approval is pending; push approval is separate.

### Prepared live configuration and bounded plan

The exact backend secret variables are **MODEL_API_KEY**, **MODAL_TOKEN_ID** and
**MODAL_TOKEN_SECRET**, supplied privately by the account owner. Public defaults remain
`MODEL_API_BASE_URL=https://api.meta.ai/v1` and `META_MODEL=muse-wonder-1.0`.
Keep **ALLOW_PAID_MODEL_REQUESTS=false** and **ALLOW_BILLABLE_MODAL=false** until live approval.
Process environment overrides dotenv; restart one backend after approved configuration changes.
Meta public API/model docs and Modal's credential-pair contract were rechecked on November 1;
links and the detailed operator runbook are in [OPERATIONS.md](docs/OPERATIONS.md).

Proposed limits, validated locally but not applied: `MAX_CONCURRENT_ANALYSES=1`,
`MAX_MODEL_CALLS_PER_SESSION=1`, `MAX_TESTS_PER_ANALYSIS=4`, `MAX_SANDBOXES_PER_ANALYSIS=8`,
`MAX_SANDBOXES_PER_SESSION=8`. Use one dedicated ignored report directory and one private attempt
ledger, with separate stable generation/verification keys. A restart does not authorize another
model request; the counters are process-local while accepted operation claims persist.

After approval only: one structured Meta request for four hypotheses using reviewed synthetic
sources/policy; inspect four valid unique policy-supported cases and the receipt; disable Meta;
execute the saved generation once in Modal (four Java plus four Python); disable both gates;
inspect persisted verdict/history and replay consistency; verify termination and actual billing.
Stop for incomplete generation and do not pad with offline cases or make replacement requests.
No automatic additional paid retry or ACCEPTED-claim resubmission is permitted. An in-flight
verification may finish remaining cases within the eight-execution bound after a case failure.
A policy-derived FAIL may be successful pipeline evidence; no release PASS is required.

The user must approve remote app/image provisioning, the synthetic source/policy transmission
and a **maximum dollar spend** covering inference/builds/compute before launch. No amount has
been approved; operation counts do not enforce dollars. The adapter still permits up to 6,000
completion tokens in the one model request. Inspect provider budget controls/rates before
enabling gates. Do not use the two-request live benchmark command within this scope.

### Remaining release milestones and approvals

| Milestone | State / next requirement |
| --- | --- |
| Offline readiness | COMPLETE; retain measured October 29 evidence |
| Milestone source-control safeguard | Plan ready; approve staging and the single local milestone commit |
| Private account configuration | Owner supplies three secret values locally; leave paid gates false |
| First live smoke test | Plan ready; separately approve one Meta request, four cases, eight sandbox executions, provisioning/data scope and a maximum dollar amount |
| Live smoke evidence | Pending actual generation/execution/oracle/classification/persistence/replay, cleanup and billing observations |
| Isolation/failure validation | Separately scoped and approved egress, UID/descriptor, timeout/OOM/output/descendant/cleanup checks; not established by eight fixture executions |
| AI evaluation | Independently authored held-out evaluation and measured live AI ablations remain pending; offline 10/10 is known-defect in-sample tuning |
| Public GitHub/hosted CI | Separate push/publication approval; CI has not run on the hosted service |
| Submission/demo and release decision | Final recorded demo and evidence review remain; no live/production readiness claim |

Preparation stops at the approval boundary. **No billable operation, gate enablement, provider
account change, staging, commit, push, deployment or product feature change occurred.**
