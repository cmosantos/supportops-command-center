# ADR-007: Suggested commands only and persisted human approval

Status: Accepted for Phase 2

## Decision

Represent commands as display-only value objects. Do not create any shell
executor. Persist approval/rejection against the exact action ID, version, digest,
and snapshot with approver reference, timestamp, status, and optional note.

## Consequences

Approval is traceable but never executes or authorizes automatic execution.
Approver identity is user-supplied in V1 and is not cryptographically verified.

