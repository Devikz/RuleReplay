# Policy model and classification

Only fictional flat late fees in USD are supported. The date of the loan's due obligation
selects policy, not its payment date. No balances, account identifiers, partial payments,
holidays, time zones, interest, compounding, multiple currencies or jurisdiction rules are
accepted. Unknown fields fail validation instead of silently approximating those scenarios.

`PolicySet` is a frozen tuple of frozen policies and frozen provenance. The JSON representation
remains an array. IDs and versions must be unique; approved intervals cannot overlap. Interval
start is inclusive, end exclusive; end must follow start. Approval must occur on/before the
start. A declared predecessor must exist, be approved, have a lower version and end exactly
at the new start. Gaps and drafts are representable, but cannot establish a compliance verdict.
There is one applicability dimension (due date), so conflicting account/jurisdiction selectors
are rejected as unsupported fields. Local provenance is user asserted, not authenticated approval.

The resolver uses interval predicates, never array order or the highest version alone.
`days_late = max(0, payment_date - due_date)` in Gregorian calendar days. A fee applies only
when days late **exceeds** grace. Early, same-day and exact-grace payments owe zero. Amounts
are integer cents throughout the authority path. A zero-dollar fee remains zero even when
grace expired; the explanation still reports expiration accurately.

| Ordered decision | Verdict |
| --- | --- |
| Invalid case schema | `invalid_input` (no execution) |
| Either implementation errors or times out | `execution_failure` |
| No unique approved policy covers due date | `insufficient_policy_evidence` |
| Both match oracle | `compliant` |
| Only legacy matches | `unauthorized_regression` |
| Neither matches | `both_implementations_wrong` |
| Only updated matches, legacy equals documented predecessor fee and predecessor differs from current | `authorized_policy_change` |
| Only updated matches, without that predecessor evidence | `corrected_legacy_defect` |

Execution failure has precedence over missing policy in the finding decision table. Neither
condition implies a business defect. A missing observation in a saved valid finding is corrupt
or incomplete evidence and is rejected. Replay mismatch is a separate replay outcome, never
silently converted to a business verdict.

The legacy `summary.decision` remains for API compatibility: hold for blockers, review for
unresolved/empty, otherwise pass. Consumers should use the new **`release.outcome`**:

1. FAIL when recorded observations establish regression or both-wrong (including explicitly
   labeled simulator observations).
2. REVIEW when no such defect exists but evidence is absent/invalid or execution failed.
3. UNVERIFIED when all supplied behaviors pass only in the fixture simulator.
4. PASS when all tested behaviors have successful Modal observations and adequate policy.

History returns the saved `release` advisory alongside the legacy summary. The frontend
uses one shared advisory presentation in history, workspace/evidence and the release dialog;
successful replay repeats that verdict without granting approval. Historical records with
no valid advisory display REVIEW. A PASS paired with non-Modal execution displays UNVERIFIED
as a presentation safeguard; this does not rewrite saved evidence or backend classification.
Offline hypothesis generation can feed real Modal execution; generation source alone is not
an execution attestation. Mocked PASS contract tests are not measured live results.

Every outcome is advisory, mode-scoped and test-scoped. A FAIL may coexist with evidence gaps;
its conclusive blocker is sufficient to hold while the gaps remain visible. PASS is not proof
of all possible behavior, organizational approval or a deployment instruction.

A run stores the full policy snapshot and canonical policy hash. `Store.get` and replay
recompute hashes and validate relationships; modifying current policy never changes historical
records. The oracle version is `late-fee-calendar-v1`; incompatible future implementations must
change that identifier and either supply the old evaluator or reject old replay. Legacy
explanation changes may yield explicit replay mismatches rather than rewrite history.

The classifier is versioned as `late-fee-classifier-v1`; replay rejects unknown classifier
versions. Older reports without that additive field use the existing v1 classifier contract.
Replay reports Python/supervisor fingerprint differences as `context_differences` while keeping
evidence consistency separate: historical observation replay does not execute the current runtime.
