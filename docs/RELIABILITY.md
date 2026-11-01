# Reliability and failure engineering

The backend is a synchronous, single-process local service. `Operations` bounds shared work
across generation and verification. `RunTrace` enforces the transition graph in the high-level
design. Findings are evaluated before the atomic write; only a successful write publishes the
terminal state. Conclusive FAIL with complete evidence can be COMPLETED; unresolved or simulator-only green runs are
NEEDS_REVIEW. No background queue or browser cancel API exists.

## Admission and budgets

| Limit | Default | Enforcement |
| --- | --- | --- |
| Concurrent generation/verification operations | 1 (configurable 1–4) | Nonblocking process semaphore; excess receives 429 |
| Model calls per process session | 4 (0–20) | Reserve before invoking provider |
| Sandbox reservations per process session | 64 (0–128) | Conservatively reserve per-analysis maximum; no uncertainty refund |
| Tests per analysis | 48 (1–48) | Request schema and configurable verification budget |
| Sandboxes per analysis | 32 (2–32) | Two per valid case; maximum 16 cases |
| Feedback iterations / automatic paid retries | 0 | No iterative provider loop or automatic paid retry |
| Request / model response | 256000 bytes each | Streaming counters |
| Java/Python source | 50000 characters each at API; 50000 UTF-8 bytes remotely | Pydantic then gateway |
| Remote lifetime / exec | 30s / 20s | Modal controls |
| Compilation / program | 10s / 3s | Trusted supervisor timeouts |
| CPU / RAM | 0.25 requested, 1 core limit / 128 requested, 512 MiB limit | Modal resource tuples |
| Child output files / accepted stdout | 16384 bytes per file / 256 bytes | RLIMIT_FSIZE and complete-output parsing |
| Supervisor stdout / saved record | 4096 UTF-8 bytes / 2000000 bytes | Host adapter and Store |

These are execution bounds, not an end-to-end availability SLA. Model HTTP timeout is 60s
with 10s connect timeout; it is not an absolute wall-clock deadline for a trickling stream.
Modal image provisioning and control-plane RPCs can outlast sandbox execution deadlines.
This remains a live-validation/deployment concern. Storage has a per-record limit but no total
retention quota; do not expose the service publicly.

## Idempotency and crash windows

`Idempotency-Key` is optional offline and required for live API operations. It must contain
8–128 ASCII letters/digits/underscore/hyphen. The UI supplies a fresh UUID per deliberate
submission. API clients retry the *same* request with the *same* key after transport uncertainty.
The UI does not automatically retry requests.

A SHA-256-derived path under `.local/reports/operations` is exclusively created before work.
The receipt binds request parameters plus current source and policy hashes. A completed claim
returns the same checksum-verified report across server restarts. Reusing the key with changed
context returns 409. Concurrent requests receive 429 and do not queue. Unfinished/failed claims
remain blocked (409), including a crash after external work but before report commit. This
chooses manual recovery over accidental repeat billing. Never delete claims merely to retry.

Report and operation receipt are separate atomic writes, not a transaction. A crash between them
may leave a valid report with an ACCEPTED claim. Inspect the correlation ID and cloud account,
then deliberately choose a new request only after resolving uncertainty. Claims are not signed.
Quotas reset on process restart and do not coordinate multiple workers; exactly one backend
process is supported. CLI benchmark live mode is separately gated and performs two explicit
calls; API session admission is not a global cloud-account budget.

## Failure behavior

| Failure | Behavior |
| --- | --- |
| Disabled/missing credentials | 409 before provider SDK/network access; no fake live fallback |
| Meta HTTP failure, timeout, malformed/refused/large result | Safe generation error (502); no automatic retry |
| Invalid generated cases | Counted with fixed rejection reasons; all-invalid suite rejected |
| Modal control-plane error | Typed execution error, normalized message |
| Sandbox/exec timeout | Timeout observation, execution_failure finding, REVIEW unless another verified defect exists |
| Java compile / Python process error | Safe failure observation; raw stderr excluded |
| Policy overlap / malformed input | 422; no ambiguous approved version accepted |
| Policy coverage gap | Insufficient policy evidence finding |
| Missing/corrupt/tampered report | 409; no successful replay |
| Disk failure | 503 storage_unavailable; accepted claim remains for review |
| Unexpected exception | Safe 500; no stack trace in response; category-only failure event |
| Graceful interruption | FAILED/CANCELLED trace and safe failure record when storage works |
| Hard process kill | ACCEPTED claim persists; no automatic resumption |
| Termination RPC failure | Structured cleanup warning; remote lifetime cap remains fallback |

Retries: none for billable operations. Validation and integrity failures must be corrected,
not retried blindly. A future transient retry policy needs provider idempotency guarantees and
budget accounting before adding exponential backoff; client timeouts alone do not prove that
billing did not occur.
