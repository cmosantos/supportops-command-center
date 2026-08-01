# ST-02 — SQLite Incident Lifecycle

## Status

**Ready**

## Objective

Implement local SQLite persistence and CLI-first incident lifecycle: idempotent
bootstrap, versioned migrations, incident registration/query, append-only status
history, close/reopen cycles, logical deletion, exact-action human approvals,
repositories, and transactional Unit of Work.

## Scope

### In scope

- SQLite configuration, connection factory, bootstrap, migration ledger/checksums.
- Incident create/get/list/update with optimistic version control.
- Append-only events; close, reopen, repeated cycles, latest-close duration.
- Soft delete with confirmation, reason, timestamp, and previous status.
- Approval records bound to incident/action ID/version/digest/canonical snapshot.
- Repository ports, SQLite adapters, Unit of Work, application services, CLI.
- Real-SQLite unit/contract/integration/security/smoke tests.

### Out of scope

Triaging/classification, runbooks, Streamlit, LLM/Ollama/OpenAI, network clients,
dashboard, exports, restore, physical deletion, retention jobs, authentication,
and any shell/external-command execution capability.

## Domain rules

- Statuses: `OPEN` and `CLOSED`.
- Valid transitions: create→OPEN, OPEN→CLOSED, CLOSED→OPEN.
- Closing CLOSED, reopening OPEN, or mutating a deleted incident is rejected.
- Every successful mutation and approval appends an immutable event.
- Reopening never removes prior close events; a later close becomes `closed_at`.
- Closed duration is latest `closed_at - created_at`; open incidents have none.
- Soft deletion is irreversible in V1 and excluded from operational queries.
- Approver identity is declared, not technically authenticated.
- Approval records data only and never authorizes automatic execution.

## Acceptance Criteria

1. `db init` creates a new database, applies ordered migrations, exits 0.
2. Repeated bootstrap is idempotent and creates no duplicate rows/structures.
3. Migrations have ordered unique versions and recorded SHA-256 checksums.
4. Checksum drift, missing sequence, or migration failure fails closed; partial
   work/version ledger entries are rolled back.
5. Every adapter connection enables foreign keys and a bounded busy timeout.
6. `db status` reports current/pending migrations without mutation.
7. A valid incident is created by CLI and round-trips completely from SQLite.
8. Missing/invalid fields are rejected safely with no partial write.
9. Default get/list operations exclude logically deleted incidents.
10. Updates increment optimistic version and append `INCIDENT_UPDATED` atomically.
11. Close records latest `closed_at`, increments version, appends event atomically.
12. Reopen clears current `closed_at` while preserving earlier close events.
13. Multiple close/reopen cycles remain complete and chronologically ordered.
14. Invalid transitions/conflicts leave incident and history unchanged.
15. Soft delete requires explicit confirmation and non-empty reason, records
    deletion metadata/previous status/event, and never issues physical DELETE.
16. No restore/hard-delete operation exists in CLI, use cases, or repositories.
17. History is append-only; public contracts offer no event update/delete.
18. Approval persists exact incident/action ID/version/digest/canonical snapshot,
    decision/status, declared approver, timestamp, and optional note.
19. Changed snapshot/version or another incident does not match old approval.
20. Approval/history records expose no public update/delete and trigger no action.
21. Every mutating use case uses explicit Unit of Work commit/rollback.
22. Lock/constraint/FK errors map to safe application errors without SQL, path,
    rejected sensitive payload, or traceback exposure.
23. All SQL values use parameters; dynamic identifiers use closed allowlists only.
24. CLI calls application services/composition root and contains no SQL.
25. Unit, contract, integration, CLI, security, smoke, and ST-01 regression pass
    offline using real temporary SQLite files.
26. Final diff remains inside this isolated repository; no remote or push.

## Tasks

- [ ] Confirm ST-01 regression and isolated baseline.
- [ ] Define incident/event/approval domain models and lifecycle invariants.
- [ ] Define repository, migration, and Unit of Work ports.
- [ ] Implement versioned migration artifacts and transactional runner.
- [ ] Implement connection factory with FK, timeout, and safe error translation.
- [ ] Implement SQLite repositories and Unit of Work with parameterized SQL.
- [ ] Implement lifecycle and approval application services.
- [ ] Extend composition root and CLI with database/lifecycle commands.
- [ ] Add real-SQLite contract/integration/locking/rollback/security/smoke tests.
- [ ] Update architecture, README, progress, pending, evidence, and File List.
- [ ] Run all quality gates, manual CLI lifecycle, DoD, and QA review.

## Required tests

Bootstrap nonexistent/repeated/partial; migration order/checksum/rollback; FK per
connection; valid/invalid registration; round-trip/reopen process; close/reopen
cycles/invalid transitions; soft delete/filter/audit preservation; transaction
fault rollback; controlled lock; approval exact binding/mismatch/cross-incident;
SQL injection payloads and parameterization scan; redacted errors/logs; CLI smoke;
offline/prohibited-import/API scan; full ST-01 regression.

## Dependencies

- ST-01 accepted and committed at `2b61bb4`.
- Python 3.12 and standard-library `sqlite3`; no new runtime database dependency.
- Approved architecture documents under `docs/architecture/`.

## Risks

- FK disabled per connection; migration drift; partial history commits; approval
  replay; SQL injection; hard delete; lock leakage; sensitive error output; scope
  drift. Each is a blocking QA gate with a real-SQLite or static security test.

## Dev Agent Record

### Agent

### Model

### Started At

### Completed At

### Implementation Notes

### Debug Log References

### Completion Notes

### Quality Gate Results

### Evidence References

## Change Log

| Date | Version | Description | Author |
|---|---:|---|---|

## File List

Planned; replace with the actual created/modified file list during implementation.

- `src/supportops/domain/**`
- `src/supportops/persistence/**`
- `src/supportops/repositories.py`
- `src/supportops/lifecycle.py`
- `src/supportops/bootstrap.py`
- `src/supportops/cli.py`
- `tests/**`
- `docs/architecture/**`
- `docs/testing/evidence/ST-02.md`
- `docs/progress.md`
- `docs/pending.md`
- `docs/stories/ST-02-sqlite-incident-lifecycle.md`

