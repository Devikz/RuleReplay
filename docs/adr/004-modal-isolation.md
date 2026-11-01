# ADR 004: Modal exclusively executes submitted code

Status: accepted for the local prototype, 2026-10-29.

## Context

Users may submit hostile Java/Python. Executing that source on the laptop would cross the most serious host trust boundary.

## Decision

Fresh Modal sandbox per implementation/case, blocked network, no credentials/mounts/OIDC, limited CPU/RAM/deadlines. Remote root supervisor drops child UID/GID/groups before execution.

## Alternatives

Local subprocess for uploads; local Docker images; persistent shared sandbox.

## Consequences

Small local footprint and no arbitrary host execution. Supervisor/child separation prevents shared-UID tampering with trusted parsing state. Trusted fixtures alone may run in local tests.

## Limitations

SDK mocks prove requested controls, not real enforcement. Platform/kernel isolation, image startup, egress denial and cleanup require approved live validation; program output is not attested business truth.
