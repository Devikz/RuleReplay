# Local operations

Use `python3.12 scripts/dev.py`: FastAPI 127.0.0.1:8000, Vite 127.0.0.1:5173.
Run one backend process. The app is not authenticated and is unsafe to expose to the internet.
The launcher propagates shutdown to child processes. Settings load root `.env`, with process
environment overrides. Preserve existing secret values and never paste them into chat/browser.

Both paid gates must remain false until the user approves an explicit bounded scope. Credential
presence alone does not enable either adapter. Public health exposes configuration/enabled flags,
not values. `.env.example` documents conservative budgets; new settings need a backend restart.

## Records and recovery

Default directory: `.local/reports/`, excluded from Git. Subdirectories are `runs`, `generations`,
`policy-sets`, `operations` (durable claims) and `failures` (safe failure metadata).
Evidence records are private-mode, fsynced and atomically renamed. Keep the whole directory when
backing up, and use file permissions appropriate to the trusted local account. There is no
retention scheduler or total disk quota. Inspect disk usage before long sessions; archive old
records outside the active directory only after preserving source/policy/generation context.

Unknown/corrupt record IDs return safe 409 errors. Do not edit JSON or recompute hashes to hide
an error. Preserve suspect files for inspection. A corrupt recent record currently causes the
history endpoint to fail closed rather than silently hide it; restore from backup if available.

An ACCEPTED operation claim after failure/restart means the provider outcome may be unknown.
Use its correlation ID, failure record, saved report and provider dashboard to resolve it.
Do not automatically delete claims or resend billable work. Once reviewed, choose a new explicit
operation/key if needed. Completed same-key requests reuse existing evidence. Process-local budget
reservations reset on restart; also use provider-account quotas for any approved live session.

## Observability

The `rulereplay.events` Python logger emits JSON events. Successful runs store stage history with
UTC timestamps and elapsed milliseconds, counts, mode/test source, oracle version, runtime and
supervisor hash. Generation receipts store model/prompt version, prompt hash and token counts
when returned. Verification counts only its own model invocations (zero); prior generation
usage stays in the nested receipt. No invented token or dollar figures are emitted.

Events cover transitions, evaluation counts/rejections, failure category, replay consistency and
cleanup failure. HTTP responses carry `X-Correlation-ID`; new run correlation matches its originating request; idempotent retries retain the original report correlation.
Raw provider errors, credentials, source code and full model completions are not logged. Saved
reports intentionally contain the submitted source and policy, and should remain private.

Stage elapsed timestamps and `metrics.stage_duration_ms` capture validation, execution and
evaluation durations separately. `duration_ms` ends immediately before evidence persistence;
the `evidence_persisted` event records storage latency separately. The UI exposes
advisory, run/correlation IDs, test source, execution count and local duration. It does not display
security certifications or an AI confidence score.

## Checks and feeds

Run the commands in TEST_STRATEGY.md. `scripts/security_audit.py` queries public vulnerability
feeds using locked Python dependencies and npm's lock. Findings fail CI. Feed/tool unavailability
is recorded as **UNAVAILABLE/UNVERIFIED**, with a CI warning and step summary, not a clean audit
or an application build failure. Re-run when service recovers. Details live in ignored
`.local/security/dependency-audit.json`. Bandit findings are reviewed; narrowly scoped suppressions
cover the intentional remote-only subprocess, fresh-sandbox fixed paths, noncryptographic random
sampling and false positives for disabled identity/unavailable usage metadata.

## Live validation, only after approval

Agree on model-call count, sandbox count and maximum spend before enabling gates. Start with a
small fixture suite. Check schema/finish status, compiler/runtime output, actual denied egress,
UID separation and parent-descriptor access, output overflow, timeouts, process descendants and
termination. Check the cloud dashboard for lingering resources. Record actual IDs/timing/tokens/
costs privately without credentials. Disable paid flags and restart after the approved session.

No live provider results, CI-host execution or remote deployment have been validated by local
mocks. A separate approval is needed for commits, pushes or publication.

## Prepared first live smoke test — 2026-11-01, not authorized or executed

The scope below is a proposed **single attempt**, with at most **one Meta request, four
cases and eight sandbox executions**. It uses existing endpoints and product behavior.
Commit approval and live-test approval are separate. Credentials alone authorize neither.

### Required backend configuration

The account owner supplies only these three secret values privately in the root `.env`:

| Variable | Purpose |
| --- | --- |
| `MODEL_API_KEY` | Meta Model API bearer credential |
| `MODAL_TOKEN_ID` | Modal token identifier |
| `MODAL_TOKEN_SECRET` | Matching Modal token secret |

Keep credentials out of chat, command arguments/history, frontend variables and sandbox
environment. Do not use `VITE_` prefixes or run shell `source .env`. The backend loads dotenv
itself. It uses these public defaults, which may remain as already configured:

```dotenv
MODEL_API_BASE_URL=https://api.meta.ai/v1
META_MODEL=muse-wonder-1.0
ALLOW_PAID_MODEL_REQUESTS=false
ALLOW_BILLABLE_MODAL=false
```

Endpoint/model and Meta authentication were rechecked against the official
[Meta overview](https://dev.meta.ai/docs/overview) and
[API reference](https://dev.meta.ai/docs/api-reference) on 2026-11-01. The existing adapter uses
`POST /v1/chat/completions` with structured JSON, not an additional model-list or probe request.
Modal's [Client reference](https://modal.com/docs/sdk/py/latest/Client) confirms the ID/secret
credential pair used by `Client.from_credentials`. Actual account access is still unverified.

Settings load the repository root `.env` even from a different working directory; process
environment takes precedence. A backend restart is required after configuration changes.
Today both gates are false, all three credentials are absent, and public health only exposes
enabled/configured booleans. A network-blocked local preflight proved all three variables
load from a temporary synthetic dotenv and never appear in health responses. No credentials
were requested or inserted, and the root `.env` bytes were preserved.

After live approval only, configure these existing limits for one backend process:

```dotenv
MAX_CONCURRENT_ANALYSES=1
MAX_MODEL_CALLS_PER_SESSION=1
MAX_TESTS_PER_ANALYSIS=4
MAX_SANDBOXES_PER_ANALYSIS=8
MAX_SANDBOXES_PER_SESSION=8
```

These proposed limits were validated locally with synthetic settings; they have **not** been
applied to root `.env`. Use a dedicated ignored report directory via `DATA_DIR` for this attempt,
record its absolute path privately and preserve it across any restart. Session counters reset
on restart, so durable claims and an operator ledger must bind the attempt across restarts.
Do not start a second backend or use the UI concurrently for additional operations.

### Approval scope and preflight

Obtain approval for the single Meta request, submission of the bundled synthetic source and
policy to Meta, and execution of those reviewed fixtures for four generated cases in Modal.
Approval must also cover lookup/creation of the `rulereplay-execution` app and the existing
remote Python 3.12 / Java 17 image provisioning, which may be billable independently of sandbox
runtime. No separate warmup, manual image build or connectivity execution is included.

A maximum dollar spend **has not been approved** and must be supplied before launch, including
inference, image provisioning and sandbox compute. Four cases still use the existing adapter's
6,000 completion-token ceiling. Operation counts and the 30-second sandbox lifetime are not a
dollar cap or absolute control-plane deadline. Inspect account-level billing controls before
enabling gates; Modal documents workspace usage/spend limits in
[Budgets](https://modal.com/docs/guide/budgets). These controls are account-specific and must
not be assumed configured. Record current rates/budget and stop if the approved ceiling cannot
be enforced or the required provisioning cannot fit within the approved scope.

Record the milestone commit hash, policy/source hashes, configured nonsecret limits, and a
distinct `Idempotency-Key` for generation and verification in the private attempt ledger.
Use a single direct API client. Do not run `benchmark --live`: it makes two model requests.
Do not print environment dumps, raw auth/provider errors or request headers.

### One generation, inspection, one verification

1. After approval, enable **only** `ALLOW_PAID_MODEL_REQUESTS` for the one backend process;
   leave Modal disabled. Check local health without making provider probes.
2. Send exactly one `POST /api/generate` with its recorded generation key and this body:

   ```json
   {"mode":"meta","count":4,"scenario":"payment_date_bug","policy_context":true}
   ```

   The backend makes one inference request. Save the returned generation receipt privately.
   Check model/source provenance, schema, completion status, unique accepted cases, rejection/
   duplicate counts and policy/source hashes. Require exactly four valid unique cases, zero
   rejections/duplicates, and approved policy coverage for all four before proceeding. Treat
   a short, rejected, malformed, unsupported or failed generation as an incomplete smoke test
   requiring review; do not add offline cases, pad output or make a replacement paid request.
3. Disable the Meta gate. Enable the Modal gate only for the already inspected generation,
   then restart the same single backend while preserving its report directory and attempt
   ledger. Do not regenerate after this restart. A restart does not grant a fresh budget.
4. Send one `POST /api/verify` with the distinct recorded verification key, the same scenario,
   `mode=modal` and the exact saved `generation_id`:

   ```json
   {"mode":"modal","scenario":"payment_date_bug","generation_id":"<saved 32-hex generation id>"}
   ```

   No explicit substitute `cases`, edited sources or changed policy snapshot are supplied.
   Four cases imply **eight** fresh sandbox executions: Java then Python per case. The API
   reserves all eight before starting. Execution failures may consume the remainder of this
   same bounded verification; there is no second verification or replacement sandbox attempt
   by the application. Existing Modal sandbox controls request blocked egress, no secret/env/
   volume/OIDC injection, bounded resources, remote child UID/GID separation and termination.
   Do not infer that these controls were empirically proven merely because configuration was
   accepted by the SDK.
5. Inspect actual observations, oracle/classification, release advisory, generation receipt
   linkage, persisted report/hashes and lifecycle. Four-case evidence is not a general quality
   evaluation. A policy-derived FAIL exposing a defect is a valid successful pipeline result;
   preserve the evidence-derived verdict. Do not require or manufacture PASS.
6. Disable both gates and restart before replay or browser inspection. Read history/details
   and `POST /api/runs/<saved-run-id>/replay`, which only recomputes saved evidence. Confirm
   consistency and the same release verdict through history/details/summary. Verify resources
   terminated in Modal and inspect usage/billing; do not assume the `finally` cleanup succeeded.

### Failure, evidence and stopping rules

There are **zero automatic additional paid retries**. A model timeout/refusal/429/5xx, unknown
outcome, malformed response, failed or timed-out sandbox, storage error, failed replay or
cleanup ambiguity ends further paid submissions with the appropriate failure/review evidence.
An already in-flight bounded verification may finish its remaining cases, still within eight
executions; the current product does not stop the whole suite on the first failed case. Existing
transport behavior inside provider SDK control-plane calls is not a license for the operator
or application to resubmit generation/verification or recreate paid work.

Do not automatically retry any durable ACCEPTED claim, delete receipts or create new keys to
bypass a previous attempt. Inspect the local receipt/report, correlation ID and provider state
first; any further billable attempt requires another explicitly bounded approval. If a response
is lost, a request count may have been consumed even when no complete evidence was saved.
Turn gates off, preserve evidence and resolve uncertainty without extra execution.

Retain actual case count, model/prompt/source/policy hashes, recorded usage tokens if returned,
local correlation/generation/run IDs, oracle/classifier versions, replay result and cleanup/
billing observations privately. Existing reports do not retain every provider request/resource
identifier, so capture identifiers visible in dashboards during the attempt without changing
the product or exposing credentials. Record costs only when reported; absent usage/cost is
UNVERIFIED, never an invented zero. Update PROJECT_STATUS only with observed results.

Stop after this one attempt and report. Timeout/OOM, hostile output, egress enforcement,
UID/descriptor isolation and descendant-process/cleanup probes are **separate live milestones**;
they do not fit automatically into these eight fixture executions. Independently evaluated
AI benchmark ablations, hosted CI, publication and the final recorded demo remain separate.
