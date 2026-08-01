# ADR-008: Local isolation and incremental quality gates

Status: Accepted for Phase 2

## Decision

Keep all product artifacts under `projects/supportops-command-center/`. Deliver in
small increments; each mapped test and regression must pass before the next.
Require human approval between phases and zero open critical security findings.

## Consequences

The AIOX core remains untouched. Progress may be slower, but evidence and failure
visibility are preserved.

