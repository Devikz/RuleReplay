# Evaluation protocol

The benchmark evaluates **input selection** against ten reviewed seeded fee defects and an
independent policy oracle. It does not benchmark AI superiority, general financial correctness,
security isolation or production-scale performance. `benchmark.observed` independently implements
mutants and the correct control. Neither mutant source nor catalog is sent in Meta prompts;
live generation receives only the selected demonstration sources and optional policy snapshot.

Configuration: Python 3.12, seed 20261029, 48-case maximum budget per method, bundled policy
snapshot. Recorded source/policy hashes, suites and first killing counterexamples allow checks
against accidental benchmark drift. `test_benchmark` recalculates scores and compares the stored
corpus. Invalid/missing policy evidence is excluded from scoring and reported in supported counts.

| Method | Definition |
| --- | --- |
| Conventional | 12 June due dates with delays 0, 3, 10, 14 |
| Seeded random | Unique uniform dates over 1096 days and delays -10 through 20 |
| Offline RuleReplay | Deterministic effective-date/grace/calendar neighborhoods |
| AI without policy | Same source prompt, no approved-policy context; unmeasured |
| Full Muse Wonder | Source plus approved-policy context; unmeasured |

Measured local result after hardening: **3/10, 6/10, 10/10**, respectively, with zero correct-control
false alarms. Previous offline boundaries scored 9/10; D10 survived because the leap-day case
ended on grace day rather than the first chargeable day. The revised boundary explicitly targets
that known survivor. This is **in-sample tuning**, not a held-out evaluation improvement.

Metrics in `benchmarks/results.json`:

- Fault detection rate: killed distinct mutants / ten.
- Correct-control false alarms and authorized-change false positives, with denominator count.
  An absent authorized-change example is zero checks, not evidence of perfect recall.
- Policy-boundary coverage: for each version, due dates at start minus/at/plus one day and
  delays at grace minus/at/plus one day under that version; covered targets / 12 targets.
  This is a disclosed synthetic metric, not an exhaustive path-coverage claim.
- Invalid-test and execution-failure rates: validated local cases/reviewed functions in offline
  measurement. Live generation rejection rate is separate; no Modal failure rate is inferred.
- Elapsed milliseconds: local evaluation, including simulator evidence creation/replay, not
  model latency or Modal cold start. Timing varies between runs.
- Evidence replay consistency: persisted simulator observations recomputed through oracle and
  classifier. This does not rerun Java/Python or reproduce an LLM completion.
- Costs and tokens are null where not measured. Generation receipts retain provider token usage
  only if valid counts are actually returned. No cost estimate is fabricated.

Reproduction: `uv run python -m rulereplay.benchmark`. The program rewrites the measured JSON and
Markdown report with actual local values. Unit tests compare semantic scores/suites, not timing.
`--live` requires explicit human approval and private configuration; it makes two Meta calls,
without Modal execution. A model may return fewer than 48 valid cases; actual counts must be
reported, not padded or treated as identical spent budgets. No feedback iteration is used.

Remaining scientific work: a larger independently authored held-out corpus, multiple disclosed
random seeds, repeated model runs with confidence intervals, actual token/cost measurements,
and live isolated execution. These are pending measurements, not inferred successes.
