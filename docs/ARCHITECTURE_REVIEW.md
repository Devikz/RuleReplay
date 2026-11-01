# Architecture review — 2026-10-29

Scope: all `backend/rulereplay` modules, frontend workflows/contracts/tests, fixtures,
policy data, benchmark corpus, scripts, dependency locks and CI. Existing uncommitted
hackathon work is preserved. No paid calls or Git writes are authorized.

Baseline reproduced: 106 backend tests, 90% statement coverage; seven frontend tests;
Ruff, TypeScript/Vite build, Prettier, secret scan and whitespace checks pass. `uv`
needed a writable temporary cache in this environment. No tests were removed.

| ID / severity | Component and risk | Fix / verification | Status |
| --- | --- | --- | --- |
| R1 High | Sandbox harness and child share UID; hostile child may alter harness state or spoof its output via parent file descriptors | Separate privileged supervisor from unprivileged child, drop supplementary groups/UID/GID; mock privilege and cleanup assertions | Implemented; verified locally |
| R2 High | Replay skips null cases and trusts nested hashes; incomplete findings or inconsistent snapshots can evade contextual verification | Validate evidence relationships, recompute all fingerprints and deterministic reasons; tampering regressions | Implemented; verified locally |
| R3 High | Concurrent/repeated accepted requests can multiply cloud spend after gates enabled | Shared admission limit, durable idempotency claims and session budgets; duplicate/concurrency/failure tests | Implemented; verified locally |
| R4 Medium | Offline all-green suite says pass; infrastructure failures share hold bucket with defects | Add explicit evidence-derived advisory outcome; retain legacy decision field for compatibility | Implemented; verified locally |
| R5 Medium | No durable lifecycle or correlation trace; storage failure becomes generic 500 | Validated lifecycle, safe structured errors and events; storage fault injection | Implemented; verified locally |
| R6 Medium | Security CI lacks vulnerability auditing and static security analysis; action tags mutable | Locked lightweight tools, explicit audit availability status, SHA pins and Dependabot | Implemented; verified locally |
| R7 Medium | Narrow property coverage; zero-fee oracle explanation incorrectly equates zero amount with grace not exceeded | Vary policy amounts, thresholds, dates and intervals; regression for zero fee | Implemented; verified locally |
| R8 Medium | Generated rejection counts lack reasons; provider usage/template metadata absent | Fixed rejection categories, template version and bounded token metadata | Implemented; verified locally |
| R9 Medium | Integrity primitives reside in model-generation module, reversing evidence dependency | Extract pure canonical hashing; AST boundary/cycle tests | Implemented; verified locally |
| R10 Low | Evaluation omits boundary coverage, replay and failure denominators | Add explicit measured metrics and unavailable cost/usage fields; consistency checks | Implemented; verified locally |
| R11 High residual | Local policy approval provenance is user asserted; no authentication/authorization or cryptographic signing | Clearly limit deployment to trusted single user, document remote controls required | Accepted prototype limitation |
| R12 High residual | Provider isolation and operational behavior unmeasured | Bounded approved live smoke test required; mocks prove configuration only | Gated, not performed |

Existing strengths: strict calendar/date and integer-cent contracts; approved, nonoverlapping
policy selection; independent oracle/classifier; typed model inputs without expected values;
network-disabled tests; no local submitted-code execution; conservative cloud resource caps;
atomic report writes; loopback/origin/host restrictions. Avoid replacing these mechanisms.

## Closure evidence

R1–R10 implemented and regression-tested. The final baseline and upgrade results are in
PROJECT_STATUS.md. Follow-up review also fixed raw unexpected exceptions escaping to the
ASGI logger, premature COMPLETED state when a failing run still has policy gaps, and replay
feedback hidden behind the release dialog. Regression tests cover all three.

R11 and R12 remain explicit limitations: authenticated policy authority, multi-user production
controls and real provider behavior are outside the validated local prototype. Additional known
limits are process-local budgets, two-file report/receipt crash windows, no total retention quota,
HTTP read timeouts rather than an absolute stream deadline, and potentially slow provider image/
control-plane RPCs. No live integration, public deployment or GitHub CI execution is claimed.
