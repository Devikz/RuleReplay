# ADR 001: Modular monolith

Status: accepted for the local prototype, 2026-10-29.

## Context

A local financial verification demo needs consistent policy, observation and classification contracts without operating distributed infrastructure.

## Decision

Keep one FastAPI process with typed execution/evidence ports and pure domain functions. Enforce authority imports and absence of cycles with AST tests.

## Alternatives

Microservices with queues; an entirely unstructured route module.

## Consequences

One deployment and small memory/disk footprint; direct testing of orchestration. Provider adapters remain replaceable without scattering provider logic.

## Limitations

One process is a failure domain. Admission and spending reservations are process-local; multiple workers and remote multi-user service are unsupported.
