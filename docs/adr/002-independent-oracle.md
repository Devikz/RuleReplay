# ADR 002: Independent deterministic oracle

Status: accepted for the local prototype, 2026-10-29.

## Context

Legacy behavior can be wrong and model completions can invent plausible expected values. Agreement between implementations is insufficient.

## Decision

Only validated approved structured policy plus oracle.evaluate establishes expected integer cents. The model output schema has no expected-fee or verdict field.

## Alternatives

Golden-master legacy behavior; model-generated expected results; updated implementation as its own oracle.

## Consequences

The classifier can identify authorized changes, fixed defects and both-wrong cases. Property tests target the independent calendar/fee model.

## Limitations

Independence is architectural, not proof that oracle authors made no mistakes. Only the fictional flat-fee domain is supported; policy approval identity is user asserted.
