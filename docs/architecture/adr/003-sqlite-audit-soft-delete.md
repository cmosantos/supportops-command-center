# ADR-003: SQLite with append-only audit records and logical deletion

Status: Accepted for Phase 2

## Decision

Use SQLite behind repositories. Status changes and approvals are append-only.
Deletion is logical, requires confirmation/reason/timestamp/previous state, and
is excluded from normal queries, exports, and dashboard metrics. V1 exposes no
physical delete or restore operation.

## Consequences

Auditability is preserved. Query policies must consistently apply the deleted
filter, and integration tests must cover every consumer.

