# ADR 005: Versioned immutable policy provenance

Status: accepted for the local prototype, 2026-10-29.

## Context

Payment-date selection can apply a new rule retroactively. Current policy changes must not rewrite the basis for historical findings.

## Decision

Resolve by due date against nonoverlapping approved half-open intervals; validate predecessor links. Freeze in-memory policies and save canonical content hashes plus full snapshots.

## Alternatives

Use latest version globally; free-text rule extraction as authority; mutable central policy reference in reports.

## Consequences

Each finding links to the exact policy ID/clause and run snapshot. Drafts/gaps cannot become financial approval; conflicting intervals fail validation.

## Limitations

Local approval metadata is not authenticated organizational authorization. Hashes do not stop coordinated malicious rewrites. Unsupported applicability dimensions are rejected.
