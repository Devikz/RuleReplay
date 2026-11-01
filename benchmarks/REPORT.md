# RuleReplay benchmark report

Measured on 2026-10-29. Synthetic data only.

Seed: `20261029`. Budget: 48 cases per method. Ten reviewed seeded defects.

| Method | Cases / supported | Detected | False alarms | Status |
| --- | --- | --- | --- | --- |
| Conventional examples | 48 / 48 | 3/10 | 0 | measured locally |
| Seeded random / oracle property | 48 / 48 | 6/10 | 0 | measured locally |
| RuleReplay offline boundaries (ablation) | 48 / 39 | 10/10 | 0 | measured locally |
| AI tests without policy context | — | — | — | not run — paid approval required |
| Full RuleReplay / Muse Wonder | — | — | — | not run — paid approval required |

## Interpretation and limits

- Offline boundaries were tuned after observing the D10 leap-day survivor. This is in-sample defect detection, not a held-out generalization result.
- Replay consistency measures saved simulator evidence, not code re-execution or LLM reproduction. Invalid-test and execution-failure rates cover validated local suites and reviewed mutant functions only. Costs and tokens are unavailable.
- AI ablations have no measurements until explicitly approved live Meta requests run. Offline boundary results are not evidence of Muse Wonder performance.
- Ten deliberately seeded defects in one synthetic policy domain; this is not a representative financial-software benchmark or proof of general superiority.
- All measured methods share the independent oracle as the evaluator. The comparison isolates input selection, not the quality of manually written expected values.
- Each method has a 48-case budget. Evidence gaps are excluded from defect scoring and reported as unsupported cases. False alarms use the independent correct control.
- Random sampling uses one disclosed seed; Hypothesis metamorphic tests are separate. Wall-clock times vary. No Modal latency or cost has been measured.

## Reproduction

`uv run python -m rulereplay.benchmark` writes this report and `benchmarks/results.json`, including every input and first counterexample.

`--live` makes two billable Meta requests and must only be used after explicit approval, credentials and the server-side paid gate are enabled. It does not create Modal resources. AI suites are saved with prompt hashes and model IDs.

## Defect outcomes

- **D01** Select policy by payment date instead of due date. Detected by: RuleReplay offline boundaries (ablation).
- **D02** Charge on the exact grace day (inclusive threshold). Detected by: Seeded random / oracle property, RuleReplay offline boundaries (ablation).
- **D03** Keep the five-day V1 grace period forever. Detected by: Seeded random / oracle property, RuleReplay offline boundaries (ablation).
- **D04** Apply seven-day grace retroactively to all due dates. Detected by: RuleReplay offline boundaries (ablation).
- **D05** Apply V2 only after, not on, its effective date. Detected by: RuleReplay offline boundaries (ablation).
- **D06** Subtract day-of-month values instead of calendar dates. Detected by: Seeded random / oracle property, RuleReplay offline boundaries (ablation).
- **D07** Reverse payment and due dates in lateness calculation. Detected by: Conventional examples, Seeded random / oracle property, RuleReplay offline boundaries (ablation).
- **D08** Charge USD 25 per late day instead of a single fee. Detected by: Conventional examples, Seeded random / oracle property, RuleReplay offline boundaries (ablation).
- **D09** Charge USD 30 instead of USD 25. Detected by: Conventional examples, Seeded random / oracle property, RuleReplay offline boundaries (ablation).
- **D10** Drop leap days from elapsed-calendar-day calculation. Detected by: RuleReplay offline boundaries (ablation).
