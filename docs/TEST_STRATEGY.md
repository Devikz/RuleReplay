# Risk-based verification strategy

The highest risks are false financial approval, authority crossing, credential disclosure,
host execution and repeat billing. Test layers exercise those contracts rather than optimizing
an arbitrary test count. The baseline 106 backend/seven UI tests are preserved.

| Layer | Concrete evidence |
| --- | --- |
| Unit | `test_engine`, `test_config`, `test_evidence`, `test_generation`: money/calendar selection, classifier branches, bounds, hashes and provider gates |
| Property | `test_policy_properties`: 300 deterministic Hypothesis examples across calendar dates, delays, grace 0–60 and fee 0–100000; 150 interval/gap/overlap examples. Hypothesis shrinks failures. Existing monotonicity/translation properties remain |
| Metamorphic | Changing case ID leaves oracle unchanged; translating dates within a policy preserves fee; later payment cannot reduce a nonnegative fixed fee; repeated evidence replay is identical |
| Mutation | Ten independently implemented reviewed mutant functions, one correct control, 48 cases per measured method. D10 regression now explicitly tests first chargeable day across leap day; measured results in benchmark files |
| API contract | Full generation-to-verification workflow, invalid schemas/origins/hosts, oversized input, unknown IDs, policy snapshots, idempotency conflicts/restarts, quotas and safe errors |
| Adversarial | `test_hardening_security`: malicious instructions in policy/source, command/verdict output fields, oversized/malformed model JSON, child identity; existing Modal timeout/output/cleanup mocks |
| Evidence negatives | `test_hardening_evidence`: outer-hash recomputation cannot hide stale nested hashes, null observations/cases, duplicate IDs, mismatched generation; changed rationale/oracle/verdict/summary/advisory fail replay |
| Integration | Mock HTTP transport uses real Meta request/validation path; injected typed gateway exercises orchestrator; real offline API and trusted Java/Python fixture execution remain covered |
| Browser | `frontend/e2e/workflow.spec.ts`: actual disposable offline API, scenario selection, findings, clause identity, advisory/mode, replay, generation and execution failure using installed Chrome; a successful offline case stays UNVERIFIED through history, evidence details, summary and replay |
| Release presentation | API history projection preserves all four backend advisories. UI tests cover PASS/FAIL/REVIEW/UNVERIFIED across saved views/replay, missing/invalid verdicts, non-Modal PASS guards and replay mismatch; PASS payloads are synthetic contract tests only |
| Architecture | `test_architecture`: authority modules only import domain; hashing imports no application module; no package import cycles; executor cannot select policies |
| Failure engineering | `test_reliability`: semaphore contention with a controlled thread barrier, persistent claim across restart, no retry after unknown outcome, budget exhaustion, storage fault and terminal-state safety |

All Python tests remove integration credentials/paid environment settings and disable outbound
socket connections. No submitted source runs locally. Trusted checked-in fixtures are the sole
local executable demonstration inputs. Mock supervisor tests replace Popen and privilege calls;
they never run attack programs or change the host UID.

Normal commands:

```sh
uv run pytest --cov=rulereplay --cov-report=term-missing --cov-report=xml
uv run ruff check .
uv run ruff format --check .
uv run bandit -r backend -q
npm --prefix frontend test
npm --prefix frontend run format:check
npm --prefix frontend run build
npm --prefix frontend run test:e2e
python3.12 scripts/check_secrets.py
uv run python scripts/security_audit.py
uv run python -m rulereplay.benchmark
```

The browser test uses two disposable loopback ports (8011/5174), temporary reports and disabled
paid settings regardless of dotenv. It requires an existing Chrome; no browser download is
part of installation. CI targets Ubuntu 24.04 with Java setup and the preinstalled Chrome listed in the
[official runner inventory](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md).
GitHub CI has not itself run because no push was authorized.

Coverage is a diagnostic, not proof. CI requires 90% statements to prevent regression from the
baseline; oracle/classifier branch behavior is explicitly tested. Mock network-block assertions
show requested configuration, not real egress enforcement. Property examples model only the
supported single-fee domain. Benchmarks are deliberately synthetic and in-sample. Reports of
success must distinguish local tests, mocks, live providers and unavailable checks.
