# Research-informed implementation

RuleReplay uses research ideas as engineering techniques, without claiming a new algorithm or copying reference implementations.

- **Mutation testing:** ten small, reviewed faults model policy-date selection, threshold changes, calendar arithmetic and fee defects. The benchmark counts a mutant as detected only when an actual input produces an observation different from the independent oracle. First counterexamples and surviving mutants are saved.
- **Metamorphic testing:** Hypothesis tests verify monotonic lateness, a bounded single fee, and invariance when both dates shift within the same policy period. These relations complement exact example assertions. The benchmark's seeded uniform random generator is explicitly separate from Hypothesis.
- **Counterexample reduction:** a domain-specific bounded scan reduces payment delay while holding the due date and discrepancy classification fixed. It reports its restricted search scope; it is not a general implementation of `ddmin` and does not claim global minimality.
- **Context ablation:** the prepared live benchmark uses the same model and case budget with versus without approved policy context. Both are evaluated using the same independent oracle. They are unmeasured until real, approved provider requests occur.

Execution-feedback-guided iterative AI generation is deferred. No untested iterative agent loop is presented as implemented.

## Primary references

- Zeller and Hildebrandt, *Simplifying and Isolating Failure-Inducing Input*, IEEE Transactions on Software Engineering (2002): [author publication page](https://www.st.cs.uni-saarland.de/papers/tse2002/). Motivates reducing a failing example while preserving the failure.
- Chen, Tse and Zhou, *Metamorphic Testing and Beyond*: [University of Hong Kong publication page](https://i.cs.hku.hk/~tse/Papers/2000s/sbeyondSTEP.html). Describes follow-up cases and properties across inputs.
- Hypothesis authors, [integrated shrinking](https://hypothesis.works/articles/integrated-shrinking/) and [official source and documentation](https://github.com/HypothesisWorks/hypothesis). Used as the property-testing dependency; no shrinking implementation copied.

The benchmark is a small synthetic engineering exercise, not a peer-reviewed evaluation. Its domain overlap with the boundary generator, one disclosed random seed, and unmeasured live integrations limit generalization. See [the measured report](../benchmarks/REPORT.md).
