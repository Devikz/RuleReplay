# ADR 007: Explicit offline and live verification modes

Status: accepted for the local prototype, 2026-10-29.

## Context

A useful demo must run without credentials, while mock outcomes must not be represented as measured cloud verification.

## Decision

Expose offline_boundary/simulator provenance; gate Meta/Modal independently. Derive advisory PASS/FAIL/REVIEW/UNVERIFIED from evidence and execution mode, with no automatic approval.

## Alternatives

Silent mock fallback on network failure; an AI confidence percentage; disabling all functionality without cloud credentials.

## Consequences

Offline failures still reveal defects in reviewed simulation, while green offline results remain UNVERIFIED. Rejected generated inputs and infrastructure errors require review.

## Limitations

Live mode only verifies supplied cases under supplied policy evidence. Historical summary.decision remains for compatibility; consumers should use release.outcome and inspect mode. Evidence replay never claims code re-execution or LLM reproducibility.
