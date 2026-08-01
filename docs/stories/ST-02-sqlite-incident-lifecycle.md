# ST-02 — SQLite Incident Lifecycle

## Status

**Done**

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

- [x] Confirm ST-01 regression and isolated baseline.
- [x] Define incident/event/approval domain models and lifecycle invariants.
- [x] Define repository, migration, and Unit of Work ports.
- [x] Implement versioned migration artifacts and transactional runner.
- [x] Implement connection factory with FK, timeout, and safe error translation.
- [x] Implement SQLite repositories and Unit of Work with parameterized SQL.
- [x] Implement lifecycle and approval application services.
- [x] Extend composition root and CLI with database/lifecycle commands.
- [x] Add real-SQLite contract/integration/locking/rollback/security/smoke tests.
- [x] Update architecture, README, progress, pending, evidence, and File List.
- [x] Run all quality gates, manual CLI lifecycle, DoD, and QA review.

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

@dev — Dex

### Model

GPT-5 Codex

### Started At

2026-08-01

### Completed At

2026-08-01

### Implementation Notes

- Implemented only the binding `OPEN/CLOSED` state machine.
- Added stdlib SQLite connection factory, FK/busy timeout/WAL, checksummed ordered
  migrations, non-mutating status, explicit transactions, and Unit of Work.
- Added incident/event/approval models, allowlisted optimistic updates,
  append-only audit records, close/reopen cycles, and irreversible logical delete.
- Exact approvals bind incident/action/version/digest/canonical snapshot and only
  record a declared, unauthenticated identity; they trigger no action.
- CLI contains no SQL and all values handled by repositories use parameters.

### Debug Log References

- `apply_patch` failed with Windows `CreateProcessWithLogonW`; authorized localized
  PowerShell fallback used and every batch checked with `git diff --check`.
- First partial Ruff run: 25 findings; all corrected. MyPy partial was green.
- First full run: MyPy 4 test typing errors and Pytest 3 obsolete ST-01 expectations;
  corrected without weakening shell/network/LLM prohibitions.
- Additional edge-test run missed one import; corrected. Final gates are green.
- CodeRabbit exit 1: WSL `/bin/sh: bash: not found`; manual DoD and independent QA
  re-review completed with PASS.

- QA fix debug: initial DDL/model replacement missed due line endings; a subsequent
  regex fallback consumed capture markers and was explicitly restored. Final syntax,
  Ruff, MyPy, Pytest, build, and CLI smoke all passed.

### Completion Notes

- All 26 acceptance criteria addressed with real temporary SQLite tests.
- 41 tests pass, including all 22 ST-01 tests and 19 ST-02 additions.
- QA regressions prove deterministic event sequencing, APPROVED-only matching,
  atomic rollback after projection mutation, and FK rejection of orphan events.
- Real CLI lifecycle and clean-wheel bootstrap demonstrations passed.
- No restore, physical delete, additional status, triage, UI, LLM, network, or
  command-execution capability was introduced.

### Quality Gate Results

- Ruff: exit 0, all checks passed.
- MyPy strict: exit 0, no issues in 28 source files.
- Pytest: exit 0, 41 passed in 1.23s.
- Build: exit 0, sdist/wheel 0.2.0.
- Clean install/smoke on CPython 3.12.12: exit 0.
- Git diff check: exit 0.
- DoD: all applicable items passed; no project coverage threshold exists.

### Evidence References

- `docs/testing/evidence/ST-02.md`

## QA Review Results

- Verdict: **PASS**.
- Acceptance criteria: **26/26 passed**.
- Automated regression: **41/41 tests passed**.
- Severity findings: **0 Critical, 0 High, 0 Medium**.
- Confirmed regressions: deterministic event sequence, APPROVED-only matching,
  atomic rollback after projection mutation, and orphan-event FK rejection.
- Independent final gates: Ruff exit 0; MyPy exit 0 (28 files); Pytest exit 0;
  real SQLite CLI lifecycle exit 0; `git diff --check` exit 0.

## Change Log

| Date | Version | Description | Author |
|---|---:|---|---|
| 2026-08-01 | 0.2.0 | Development started (interactive mode) — Status: Ready → InProgress | @dev |
| 2026-08-01 | 0.2.0 | Development complete — Status: InProgress → InReview | @dev |
| 2026-08-01 | 0.2.1 | QA fixes started — Status: InReview → InProgress | @dev |
| 2026-08-01 | 0.2.1 | QA blocking fixes complete — Status: InProgress → InReview | @dev |
| 2026-08-01 | 0.2.1 | QA re-review PASS — Status: InReview → Done | @qa / @devops |

## File List

- `.env.example`
- `README.md`
- `docs/architecture/contracts.md`
- `docs/architecture/sqlite-schema.md`
- `docs/pending.md`
- `docs/progress.md`
- `docs/stories/ST-02-sqlite-incident-lifecycle.md`
- `docs/testing/evidence/ST-02.md`
- `src/supportops/__init__.py`
- `src/supportops/bootstrap.py`
- `src/supportops/cli.py`
- `src/supportops/config.py`
- `src/supportops/domain/incidents.py`
- `src/supportops/errors.py`
- `src/supportops/lifecycle.py`
- `src/supportops/persistence/__init__.py`
- `src/supportops/persistence/database.py`
- `src/supportops/persistence/migrations.py`
- `src/supportops/repositories.py`
- `tests/cli/test_cli.py`
- `tests/cli/test_sqlite_cli.py`
- `tests/integration/test_lifecycle.py`
- `tests/integration/test_migrations.py`
- `tests/security/test_prohibited_apis.py`
- `tests/security/test_sqlite_safety.py`
- `tests/smoke/test_startup.py`