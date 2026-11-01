# ADR 003: Meta plans tests, never release verdicts

Status: accepted for the local prototype, 2026-10-29.

## Context

Source-aware input generation may find migration boundaries, but instructions inside source/policy prose are attacker-controlled data.

## Decision

Call Muse Wonder only for structured test hypotheses, with trusted developer instructions separated from user JSON; validate and deduplicate all inputs. No tools or shell commands are granted.

## Alternatives

Agentic execution loop; unconstrained generated test code; offline heuristics only.

## Consequences

Prompt injection cannot directly set an authoritative verdict or execute tools. Preserve model, prompt version/hash, rejection reasons and returned token counts.

## Limitations

Good schemas cannot guarantee good test coverage or truthful analysis prose. Live model quality/latency/cost remain unmeasured; no automatic paid retries.
