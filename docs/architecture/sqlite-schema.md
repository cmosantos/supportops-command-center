# SQLite Schema Design

Status: ST-02 implemented subset; later tables remain proposed.

## Conventions

- SQLite foreign keys enabled on every connection.
- UTC timestamps stored as ISO-8601 text.
- IDs stored as opaque text primary keys.
- Check constraints protect finite state fields.
- Writes use explicit transactions and bound parameters.
- Migrations are versioned, forward-only in normal operation, with documented
  backup/rollback steps before destructive schema evolution.

## Tables

### `schema_migrations`

`version` PK, `description`, `applied_at`, `checksum`.

### `incidents`

Core columns: `id` PK, intake fields, category/subcategory, impact, urgency,
priority, recommended level, escalation flag, status, `created_at`, `updated_at`,
`closed_at`, actor references.

Soft-delete columns: `deleted_at`, `deletion_reason`, `deletion_confirmed`,
`pre_deletion_status`.

Constraints ensure valid enums and complete deletion metadata as a group.
Default query policy adds `deleted_at IS NULL`.

Indexes:

- `(created_at)`
- `(category, deleted_at)`
- `(priority, deleted_at)`
- `(status, deleted_at)`
- `(closed_at)` for closed-incident metrics

### `incident_status_events`

`id` PK, `incident_id` FK, previous/new status, timestamp, actor, reason.
Delete behavior is restricted. Index `(incident_id, changed_at)`.

### `triage_results`

`id` PK, `incident_id` FK, classification fields, rationale,
`priority_matrix_version`, `created_at`. Results are snapshots and append-only.

### `diagnostic_questions`

`id` PK, `incident_id` FK, topic, question, required evidence, reason, blocking
flag, answer, answered_at, created_at.

### `hypotheses`

`id` PK, `incident_id` FK, statement, justification, evidence, confidence,
verification, discard condition, status, sources JSON, timestamps.
Confidence constrained to `[0,1]`.

### `troubleshooting_plans`

`id` PK, `incident_id` FK, `created_at`, escalation criteria JSON, revision.

### `troubleshooting_steps`

`id` PK, `plan_id` FK, sequence, phase, objective, instruction, expected result,
risk, admin flag, approval-required flag, rollback, sources JSON. Unique
`(plan_id, sequence)` and phase check constraint.

### `command_suggestions`

`action_id`, `version` composite PK, `incident_id` FK, command text and required
metadata, action digest, created_at. No execution state exists.

### `human_approvals`

`id` PK, `incident_id` FK, action ID/version, action digest/snapshot, decision,
approver reference, decided_at, note, created_at. Composite FK targets the exact
command suggestion. Decision values are pending/approved/rejected.

### `performed_procedures`

`id` PK, `incident_id` FK, optional action reference, description, result,
performed_at, actor reference. This table distinguishes claimed performed work
from suggestions; the application records user reports only.

### `incident_documentation`

`id` PK, `incident_id` FK, revision, nine required document sections,
`created_at`. Unique `(incident_id, revision)`.

## Query policies

1. Normal incident/history/dashboard/export queries exclude soft-deleted rows.
2. An explicit audit repository query may include deleted rows.
3. A deleted incident cannot be restored in V1; no restore use case is exposed.
4. Single-incident export rejects a deleted incident in normal mode. Audit export
   is out of scope for V1.
5. Dashboard metrics exclude deleted incidents consistently.

## Status state machine

Allowed transitions:

- `open -> in_progress | resolved | closed`
- `in_progress -> resolved | closed`
- `resolved -> in_progress | closed`
- `closed -> reopened`
- `reopened -> in_progress | resolved | closed`

Every transition atomically updates `incidents.status` and appends one status
event. Invalid transitions roll back.

## Concurrency and lifecycle

Adapters use short-lived connections, a configurable busy timeout, WAL mode when
validated for the target volume, explicit transaction boundaries, and retry only
for known transient lock errors. Streamlit sessions never share mutable cursors.

## Bootstrap and verification

Future implementation will create the database and apply pending migrations
idempotently at CLI/Streamlit startup. Integration tests will use a real temporary
SQLite file and verify foreign keys, constraints, rollback, locking behavior, and
automatic creation. No executable SQL is part of Phase 2.



## ST-02 implemented subset

ST-02 implements only OPEN and CLOSED, with OPEN -> CLOSED and CLOSED -> OPEN. The broader conceptual states above remain unimplemented future design and must not be inferred as current behavior. Migrations are ordered Python artifacts with SHA-256 checksums and statement-by-statement explicit transactions; executescript is not used.

The incident_events implementation uses a positive per-incident sequence with a unique constraint. The next value is calculated and inserted inside the same write transaction, and history orders by sequence rather than timestamps or opaque IDs.

## ST-03 implemented subset

Migration 2 creates `triage_snapshots` with:

- opaque snapshot ID and incident FK with `ON DELETE RESTRICT`;
- positive `sequence` unique per incident;
- policy/schema/matrix versions and a 64-character policy checksum;
- JSON-valid input, full result, missing evidence, questions, risk, stop and
  escalation reason snapshots;
- constrained complete/incomplete outcome, priority, route and escalation flag;
- UTC creation timestamp and optional declared actor.

A complete row requires priority and route; an incomplete row requires both to be
NULL. Sequence is calculated with `MAX(sequence)+1` inside `BEGIN IMMEDIATE`.
The repository exposes insert/list/latest only and orders by sequence. The result
and all questions are inserted atomically; injected failures roll back the row.
