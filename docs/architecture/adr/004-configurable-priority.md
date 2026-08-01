# ADR-004: Configurable deterministic priority matrix

Status: Accepted for Phase 2

## Decision

Calculate P1-P4 from a single versioned, schema-validated impact-by-urgency
configuration. Invalid/incomplete configuration fails startup safely. The full
matrix and boundary cases require Support Specialist approval before coding.

## Consequences

Rules are not scattered through code and changes are testable. Configuration
governance and version-linked triage snapshots are required.

