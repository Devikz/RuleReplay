# Security review and live-validation boundary

Reviewed locally on 2026-10-29. No paid cloud resources or inference requests were created during implementation.

## Implemented and tested

- Existing ignore rules retained. `.env`, variants, virtual environments, dependency folders, local reports and build/cache artifacts excluded; `.env.example` remains trackable.
- Root `.env` mode 0600, empty credentials preserved, private values never printed. Backend settings use `SecretStr`, exclude credentials from serialization, and expose only configured/enabled booleans to the UI.
- Paid model and Modal flags default false. Credential presence alone is insufficient. No browser/API route can flip a gate. Tests strip integration environment variables and prohibit outbound Python sockets.
- Official Meta URL/model enforced; no custom destination, redirect, shell execution, logging of auth headers, or automatic paid retry.
- Submitted code cannot enter local simulator execution. Only fixed reviewed repository fixtures run on the host during tests. Actual arbitrary-code path is Modal only.
- Sandbox creation specifies blocked networking, no secrets/env credentials/identity token/volumes, 30-second lifetime, up to one CPU and 512 MiB. Compile deadline 10 seconds, execution 3 seconds, outer harness command 20 seconds. Code runs as a non-root user with capped output files, CPU, file descriptors, process count and no core dumps.
- Process groups are killed on timeout and after completion. Sandbox termination is attempted in `finally`; a provider cleanup failure still leaves the lifetime cap. Output is capped while streaming back to the backend. The harness rejects oversized stdout before parsing rather than validating a truncated prefix. Actual Modal SDK timeout exceptions and its timeout return code are classified as timeouts. Raw stderr and provider exceptions are not sent to the browser.
- Evidence IDs are validated; writes are atomic, and reads verify content hashes. Untrusted browser origins, untrusted host headers, and oversized request bodies are rejected. Validation responses do not echo input values.
- Frontend uses React text rendering, never unsafe HTML insertion. Vite's environment root is the frontend directory, with no backend secret variables exposed.

## Limits requiring validation or production work

Modal image availability, remote non-root execution, actual network egress denial, platform timeout behavior and cleanup have only been checked against documentation/SDK contracts and mocks. They need an approved live run. The harness protects the host and limits resources; it is not an attestation system proving that adversarial programs cannot forge outputs inside their own sandbox. The application trusts observations as program outputs, not as policy truth.

A local file owner can rewrite a record and its hash. Hashes are not signatures. Synthetic approval metadata is not identity-verified. Local storage has no tenant isolation or authentication and must not be exposed publicly. Request-size and per-run bounds are not organization-wide spending quotas. The server's paid flags authorize subsequent local requests, so enable them only for an agreed scope and disable them afterward.

## Remaining approval checklist

After the user privately enters `MODEL_API_KEY`, `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` and explicitly approves an agreed test budget:

1. Enable only the required paid flag(s), restart the backend, and make one bounded Muse Wonder generation request; inspect schema, finish status, model and provenance.
2. Run a small Modal suite with the original fixtures, verifying compilation, correct observations, timeout, stdout limits, blocked network and no secret injection. Confirm sandbox termination in Modal.
3. Run the two AI benchmark ablations; publish only measured outcomes with their generation receipts.
4. Review the concrete diff and documentation before separately approving a GitHub push or publication.

No step above has been performed or silently authorized by the implementation.

## Senior hardening changes

The remote supervisor now runs as root **inside Modal only**, while its child drops all
supplementary groups and switches GID/UID to 65534 before executing submitted code. This separates
supervisor memory/files/descriptors from child ownership. The work directory is owned by the
child; the supervisor script remains root-owned. A fresh sandbox is used per language/case.
The image has no host workspace mount. Actual permission and network behavior remains live-gated.

New controls include shared admission, bounded per-session cloud reservations, required live
idempotency keys, deep immutable policy contracts, nested evidence/context verification, safe
failure records and explicit advisory outcomes. Corrupt or incomplete observations cannot be
replayed as compliant. Simulator-only green runs are UNVERIFIED; infrastructure failures require
REVIEW, unless a separate recorded policy violation already makes the run FAIL.

CI uses read-only permissions, verified commit pins for actions, no persisted checkout credential,
no provider secrets, locked dependencies, Bandit and Python/npm vulnerability auditing. Secret
checks cover known local credentials, common GitHub/AWS/private-key patterns and empty example
credential fields. Pattern scanning is a useful gate, not exhaustive secret discovery. Audit feed
unavailability is explicitly unverified and is distinct from reported vulnerabilities.

See [THREAT_MODEL.md](THREAT_MODEL.md) for STRIDE/OWASP mapping, [RELIABILITY.md](RELIABILITY.md)
for bounds and crash windows, and [OPERATIONS.md](OPERATIONS.md) for recovery. Fixed sandbox paths
and subprocess calls have line-specific Bandit suppressions because they are intentional remote
supervisor operations; no global subprocess/security rule has been disabled.
