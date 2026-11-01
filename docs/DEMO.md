# Three-minute demo script

Use the working local workspace. Keep **Trusted fixture simulator** and **Offline deterministic boundaries** selected unless live calls have separately been approved and tested. Do not describe local simulation as Modal execution or offline generation as AI output.

| Time | Action and narration |
| --- | --- |
| 0:00–0:20 | “Your code passed the tests. But did it follow the rules? Financial migrations can preserve the wrong behavior—or change behavior for a perfectly valid reason. RuleReplay makes the difference visible.” Point to Java, Python and the independent policy oracle. |
| 0:20–0:45 | Open Policy library. “This fictional late-fee policy extends grace from five days to seven starting November 1. The decisive date is the loan due date. Every rule has an effective period and approval provenance.” |
| 0:45–1:05 | Open Test generation and generate 16 offline hypotheses. “Our Meta Muse Wonder integration generates structured boundary hypotheses. Today this labeled offline suite runs without credentials or spend. The AI never supplies authoritative expected fees.” |
| 1:05–1:35 | Verify the suite (or choose **Run current draft** in the workspace). Inspect boundary-01: due October 30, paid November 5. “Legacy charges $25; the update charges zero because it mistakenly chooses policy by payment date. The independent oracle selects V1 using the due date, proves six days exceeds five, and classifies an unauthorized regression.” |
| 1:35–1:55 | Inspect boundary-02: due November 1, paid November 7. “The same $25-to-zero change is correct here. Approved V2 provides seven days. The predecessor link explains an authorized policy change, not a bug.” |
| 1:55–2:15 | Change scenario to Legacy threshold defect corrected; run. Inspect an exact five-day case. “The update also fixes a legacy off-by-one defect. Historical cases without approved coverage remain unresolved rather than receiving invented expectations.” |
| 2:15–2:35 | Return to Payment-date policy bug, run, open Release summary. “The backend release verdict is FAIL for this regression. Successful offline cases remain UNVERIFIED, including in history. Replay checks saved evidence consistency; it does not re-execute code or approve a release.” |
| 2:35–2:50 | Open Benchmarks. “Conventional: 3/10. Random: 6/10. Offline targeted boundary tests: 10/10. This is an in-sample, known-defect benchmark with tuning against the leap-day survivor. Muse Wonder results remain unmeasured.” |
| 2:50–3:00 | “Beyond Assertions connects model-generated hypotheses with deterministic policy evidence and isolated execution. The goal is not more alerts: it is a justified decision about whether a software change follows the approved rule.” |

## Other quick demonstrations

The benchmark was rerun on 2026-10-29 with equal 48-case budgets (48, 48 and 39 policy-supported cases respectively). The earlier 9/10 offline result preceded deliberate tuning against D10. The current 10/10 measures deterministic offline input selection, not Muse Wonder performance or superiority over baselines. Live, independently evaluated AI results are required before making either claim; see [EVALUATION.md](EVALUATION.md).

- **Both implementations wrong**: agreement does not imply compliance.
- **Execution failure**: a failed calculation cannot become a zero fee.
- **Minimize counterexample**: finds the smallest nonnegative delay at the fixed due date preserving a local-simulation regression (bounded to 90 days).
- **Policy editor**: overlapping approved periods are rejected; valid edits create an immutable snapshot.
- **Source editor**: editing source makes Modal required; no arbitrary code runs on the MacBook.

## Submission readiness

Local demo and documentation are available. Live Meta and Modal validation, live AI benchmark results, final video capture, and GitHub publication remain outstanding. Do not claim those completed based on mocked tests or this script.
