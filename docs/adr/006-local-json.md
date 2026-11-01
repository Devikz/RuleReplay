# ADR 006: Atomic local JSON evidence

Status: accepted for the local prototype, 2026-10-29.

## Context

A single-user demo needs portable inspectable evidence and restart-safe duplicate-request handling without a database service.

## Decision

Private local files, canonical SHA-256, fsync and atomic rename; nested context validation on read. Use exclusive operation claims for keyed requests and block uncertain retries.

## Alternatives

SQLite transactional storage; remote object store; mutable in-memory reports.

## Consequences

Simple export and backup; no heavy service. Source/policy snapshots and deterministic replay expose accidental modifications and internally inconsistent records.

## Limitations

No transaction spans report and claim; a crash between writes requires manual recovery. No signatures, tenant isolation, automatic retention or total disk quota. SQLite is the next step if concurrency/retention requirements grow.
