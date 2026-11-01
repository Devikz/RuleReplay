# Practical threat model

Reviewed 2026-10-29. Assets are policy authority, truthful findings, credentials, cloud budget,
local workspace integrity and replayable evidence. The supported deployment is one trusted
local user. Attackers may control submitted source, policy prose, generated inputs/model
responses, browser requests, stdout/stderr or saved artifacts. Local machine administrators
can rewrite code, policies and hashes; this design does not defend against that actor.

## Boundaries and STRIDE assessment

| STRIDE | Attack / component | Controls and verification | Residual risk |
| --- | --- | --- | --- |
| Spoofing | Malicious website invokes paid localhost API | Host and exact-origin checks; private gates; live idempotency key; API negative tests | Not authentication. Local processes can call API; never expose publicly |
| Spoofing | Model declares approved policy or compliant verdict | Extra fields rejected; oracle uses independently validated snapshot; injection tests | Model can still propose poor inputs or misleading analysis prose |
| Spoofing | Child writes fake harness envelope through parent descriptors | Root remote supervisor; child drops groups/GID/UID; subprocess capture and strict parsing; mocked privilege assertions | Live Linux permission behavior needs validation; a program can always lie about its own fee |
| Tampering | Overlap or payment-date policy selection | Frozen structured policy, unique IDs/versions, half-open interval checks; property tests | A trusted local user can submit false approval provenance |
| Tampering | Edited saved source/policy/observation/verdict | Outer hash, nested context hashes, complete findings, deterministic replay; rehashed-envelope negative tests | Attacker able to consistently rewrite all data and hashes is not detectable |
| Tampering | Edited generation reused for different source/policy | Generation fingerprint binding and nested receipt integrity; API/context tests | No external signing or independent append-only store |
| Repudiation | Repeat cloud request after timeout | Durable keyed claim, correlation trace, conservative reservation; interruption/restart tests | Provider receipts/costs and signed audit trails not implemented |
| Information disclosure | Provider error includes key/source | Fixed sanitized errors, no raw exception/model/source logs, secret tests | User-selected source is deliberately sent to Meta/Modal in live mode |
| Information disclosure | Sandbox reads credentials or host files | Empty secrets/env, OIDC disabled, no mounts; mock create-argument tests | Cloud platform isolation remains an external dependency |
| Denial of service | Huge/chunked browser/model payload | Size limits, count/date bounds, output caps and schema validation | Body timeout and total stored-file retention remain local deployment limits |
| Denial of service | Repeated or parallel paid work | Nonblocking admission, session budgets, live key requirement; budget/concurrency tests | Budgets reset on restart; cloud-account budget must also be set |
| Denial of service | Fork/output/CPU abuse | Fresh sandbox, limits for CPU/RAM/processes/files/open FDs, deadlines, descendant cleanup | Platform quotas, image cold starts and control-plane outages require live checks |
| Elevation of privilege | Prompt asks model to execute shell | Model has no tools; returns typed dates/IDs only; no generated command execution | Prompt text alone cannot guarantee model behavior |
| Elevation of privilege | Submitted code escapes child identity | Privilege drop in remote supervisor; no local execution; no root workspace mounts | Not a sandbox-escape proof; depends on Modal/kernel isolation |

## OWASP GenAI mapping

The [official OWASP LLM Top 10 page](https://genai.owasp.org/llm-top-10/) retrieved on the
review date lists the **2025** edition. This assessment uses that source, rather than
unverified secondary claims about another edition. The applicable categories include prompt
injection (LLM01), sensitive information disclosure (LLM02), supply chain (LLM03), improper
output handling (LLM05), excessive agency (LLM06), misinformation (LLM09) and unbounded
consumption (LLM10). RuleReplay has no RAG/vector store or model training pipeline.

[OWASP prompt-injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
informs the separation of trusted developer instructions from untrusted user-data JSON.
The enforceable controls are downstream: no tools, no expected-output fields, strict typed
inputs and an independent oracle. The model's prose remains untrusted and is not a release
confidence score. React renders it as text rather than HTML.

## Modal boundary

[Modal networking documentation](https://modal.com/docs/guide/sandbox-networking) states
that default egress is allowed and `block_network=True` blocks outbound access. RuleReplay
sets it explicitly. The [Sandbox reference](https://modal.com/docs/sdk/py/latest/Sandbox)
defines lifetime, CPU/memory limits, secrets, environment and identity options. The adapter
uses fresh sandboxes, no volume mounts, empty credentials/environment and no OIDC injection.

Tests verify arguments, timeout mapping, complete stdout parsing, process-group cleanup,
child privilege-drop order and SDK filesystem availability. They do **not** establish that
an actual hostile network attempt was blocked by Modal. An approved live check must test
network denial, attempts to modify/read parent process descriptors, output flooding,
child-process cleanup, compilation, deadlines, OOM and termination errors.

No OWASP/NIST certification, penetration-test completion or production-readiness claim is made.
