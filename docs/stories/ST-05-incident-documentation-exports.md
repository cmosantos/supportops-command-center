# ST-05 — Incident documentation and safe exports

## Status

**Done**

The user explicitly authorized Increment 5 on 2026-08-02 as the first stage of
the final V1 campaign. This story authorizes Increment 5 only. Increment 6 may
start only after this story reaches Done, its local commit exists, and its gate is
green. Increment 7 remains optional and outside the campaign.

## Objective

Persist traceable reports of procedures actually performed, keep them distinct
from suggested procedures, generate revisioned nine-section incident
documentation exclusively from persisted records, and expose safe Markdown and
JSON exports through the CLI without executing any suggested or administrative
action.

## Executor Assignment

```yaml
executor: "@dev"
quality_gate: "@qa"
quality_gate_tools:
  - Ruff
  - MyPy
  - Pytest
  - build
  - CLI demonstrations
  - security review
```

## Story

**As an** N1 or N2 support analyst,
**I want** to record what was actually performed and generate traceable incident
documentation and safe exports,
**so that** I can distinguish recommendations from reported actions and transfer
an auditable, persisted account to operational ticketing systems.

## In Scope

- A typed performed-procedure report, persisted with incident reference,
  description, result, timestamp from the application clock, declared actor, and
  optional reference to a previously persisted suggested action.
- Immutable, ordered retrieval of performed-procedure reports, separate from
  suggested procedures and approvals.
- Revisioned incident documentation with exactly these nine sections:
  1. executive summary;
  2. technical description;
  3. collected evidence;
  4. evaluated hypotheses;
  5. suggested procedures;
  6. procedures actually performed;
  7. applied solution;
  8. result and preventive recommendation;
  9. GLPI/ServiceNow-ready text.
- Deterministic documentation generation from persisted, traceable incident,
  history, triage, suggestion, approval, and performed-procedure records that
  actually exist; missing optional records are represented explicitly and never
  fabricated.
- Persistence and ordered retrieval of immutable documentation revisions.
- `IncidentExporter` implementations for valid Markdown and JSON, returning
  content/bytes, media type, format, and an application-generated safe filename.
- A fixed validated export root; atomic writes whose resolved targets remain
  inside that root; callers supply incident ID and format, never a path or
  filename.
- CLI-first commands to record/list performed procedures, generate/show incident
  documentation, and export Markdown or JSON with human and machine-readable
  responses following established conventions.
- Versioned SQLite migration(s), repositories, Unit of Work integration, safe
  errors, tests, documentation, evidence, and complete ST-01–ST-04 regression.

## Out of Scope

- Streamlit, dashboard, web presentation, or any Increment 6 work.
- Ollama, OpenAI, another LLM, embeddings, vector databases, semantic RAG, or any
  Increment 7 work.
- Docker, Compose, release hardening, GitHub Actions, publication, remote setup,
  push, or any Increment 8 work.
- Shell/subprocess execution, command executor ports, administrative actions,
  automatic remediation, or treating an approval as permission to execute.
- Direct GLPI/ServiceNow integration, network access, ticket submission, or
  authentication of the declared actor.
- Audit export of logically deleted incidents, restore, physical deletion,
  arbitrary export locations, user-selected filenames, templates, or formats
  other than Markdown and JSON.
- New hypothesis, troubleshooting-plan, dashboard, retention, or business-policy
  behavior not already represented by persisted V1 records.

## Rules and Safety Invariants

1. A suggested procedure is display-only guidance. A performed procedure is a
   user-reported historical fact. They use separate models, persistence records,
   application commands, CLI labels, and document sections.
2. Recording a performed procedure never runs, validates, approves, or infers the
   execution of a suggestion. An optional action reference must resolve to the
   exact persisted incident/action identity or be rejected atomically.
3. Procedures performed, documentation revisions, and export provenance are
   traceable to the incident and ordered deterministically; existing records are
   not overwritten or deleted.
4. Documentation is assembled only from records read through repositories for
   the requested, non-deleted incident. CLI arguments, process state, runbook
   files, or unpersisted values cannot be inserted as incident facts.
5. The nine required sections are always present in their defined order. Empty
   source collections use explicit neutral wording; the generator never invents
   evidence, hypotheses, procedures, solution, result, or ticket actions.
6. Generation creates the next immutable positive per-incident revision inside
   one transaction. A failure rolls back the revision completely.
7. Export reads a persisted documentation revision. It does not silently
   regenerate, mutate the incident, or export a logically deleted incident.
8. The application owns the export root and generated filename. Filename
   components use a closed safe character policy and cannot contain separators,
   drive prefixes, control characters, dot segments, or user-controlled paths.
9. Before writing, the exporter resolves root and target and proves target
   containment beneath the fixed root. Traversal, absolute/UNC paths, alternate
   separators, symlink/reparse escapes, collisions, and invalid roots fail safely.
10. Markdown rendering treats all persisted text as inert content and preserves
    section structure safely. JSON output is standards-compliant UTF-8, schema-
    stable, deterministic, and parseable by a strict JSON parser.
11. Exports and user-facing errors do not disclose absolute filesystem paths,
    SQL, stack traces, secrets, configuration values, or unrelated incident data.
12. CLI presentation contains no SQL, document assembly rules, filename rules,
    filesystem writes, or export serialization; it delegates to application
    services and ports through the composition root.
13. No shell, subprocess, dynamic evaluation/import, network client, LLM, UI, or
    administrative execution capability is introduced.

## Acceptance Criteria

1. A strict typed `PerformedProcedure` (or equivalently named domain model)
   records an opaque ID, incident ID, non-empty description, non-empty result,
   UTC `performed_at` from the injected clock, declared actor reference, and an
   optional exact persisted suggestion/action reference; password/token fields do
   not exist.
2. Suggested procedures and performed procedures remain structurally and
   behaviorally separate in models, storage, services, CLI output, documentation,
   and JSON. Recording performed work cannot mutate suggestions or approvals and
   cannot trigger execution.
3. A versioned forward-only SQLite migration creates constrained
   `performed_procedures` and `incident_documentation` storage with incident
   foreign keys, positive per-incident ordering/revision, required fields, useful
   indexes, and migration checksum/rollback behavior consistent with ST-02/03.
4. Recording a valid performed procedure for an operational incident commits the
   row and its traceability data atomically; invalid incident, deleted incident,
   empty fields, invalid actor/timestamp, cross-incident or nonexistent action
   reference, constraint failure, and injected persistence failure leave no
   partial row and return a safe typed error.
5. Performed-procedure history is immutable, scoped to one operational incident,
   returned in deterministic persisted order, and exposes no update/delete or
   executor operation.
6. A typed `IncidentDocumentation` represents one incident and revision and
   contains all nine required sections in the exact approved order, including
   distinct `suggested_procedures` and `performed_procedures` collections or
   renderable sections.
7. Documentation generation retrieves the requested non-deleted incident and all
   contributing facts through repository/application contracts and uses only
   persisted traceable records. Tests prove that unpersisted input, CLI text,
   unrelated incidents, and unavailable optional data cannot become facts.
8. Generated documentation includes: executive summary; technical description;
   collected evidence; evaluated hypotheses; suggested procedures; procedures
   actually performed; applied solution; result and preventive recommendation;
   and GLPI/ServiceNow-ready text. Each section is complete, labeled, ordered,
   deterministic for the same persisted snapshot, and safely represents missing
   source data without fabrication.
9. Suggestions and approvals, when present, remain described as suggestions and
   decisions only. The applied-solution/result sections derive exclusively from
   persisted performed reports or other explicitly persisted fields approved by
   existing contracts; approval alone is never represented as execution.
10. Each successful generation appends the next positive immutable
    per-incident documentation revision in one transaction; concurrent/failed
    generation cannot create a partial revision, overwrite history, or return a
    different incident's data.
11. Documentation history and exact revision retrieval are deterministic and
    scoped to the operational incident; logically deleted incidents are excluded,
    audit export is unavailable, and public contracts expose no revision mutation
    or deletion.
12. A replaceable `IncidentExporter` boundary remains independent of CLI and
    SQLite details. Markdown and JSON adapters serialize one persisted
    documentation revision and return artifact content, media type, format,
    generated filename, revision, and incident traceability metadata.
13. Markdown export has exactly the approved nine headings in order and safely
    renders hostile persisted Markdown/HTML/control text as inert documentation
    without creating executable behavior or corrupting section boundaries.
14. JSON export is valid UTF-8 JSON accepted by a strict parser, has a documented
    stable schema containing incident/revision provenance and all nine sections,
    preserves Unicode, and produces deterministic key/collection ordering for the
    same persisted revision.
15. Export filenames are generated solely by the application from allowlisted
    normalized components plus the incident/revision/format contract, end in
    `.md` or `.json`, are deterministic or collision-safe by documented policy,
    and never accept a caller-provided filename or path.
16. The export directory is a fixed validated application-owned root. Every
    resolved target is proven contained beneath it before an atomic write; missing
    safe roots may be initialized according to validated settings, while invalid,
    file-valued, unreadable, or escaping roots fail closed.
17. Traversal and escape attempts using `..`, absolute paths, UNC/drive paths,
    alternate separators, encoded/control characters, malicious incident IDs,
    symlinks/reparse points, nested outside-root targets, and filename collisions
    are rejected without reading, overwriting, writing, or disclosing files
    outside the export root.
18. Existing files are never silently overwritten. A failed serialization or
    write leaves no partial final artifact; temporary artifacts are safely scoped
    and cleaned or made non-observable, and returned paths are relative to the
    export root rather than absolute.
19. CLI commands support: recording and listing performed procedures; generating
    and showing persisted incident documentation; and exporting a selected/latest
    persisted revision as Markdown or JSON. Human and JSON modes expose equivalent
    provenance and safe errors with stable exit codes.
20. CLI demonstrations prove a complete persisted journey: create/use an
    incident, record performed work separately from suggestions, generate a
    revision, show the nine sections, export both formats, parse JSON, and confirm
    the files remain inside the configured root, all without UI, network, LLM, or
    action execution.
21. Empty/invalid fields, unknown/deleted incident, absent documentation revision,
    unsupported format, malformed persisted JSON/data, export-root failure, and
    write failure map to established safe application/CLI errors with non-zero
    exit codes and no SQL, absolute path, traceback, secret, or sensitive payload
    disclosure.
22. Unit, repository/contract, real-SQLite integration, CLI, export integration,
    security, and smoke tests cover separation, traceability, ordering, revision,
    rollback, Markdown/JSON validity, filenames, containment/traversal, hostile
    content, no results/absent optional records, and prohibited capabilities.
23. Ruff, strict MyPy, full Pytest regression including all 192 passing ST-01–04
    baseline tests (with only documented environment-conditioned skips), offline
    wheel/sdist build, clean installed-wheel CLI smoke, and `git diff --check`
    pass with commands, environment, exit codes, and final counts recorded.
24. Independent `@qa` functional and security review verifies every criterion and
    reports PASS with zero open Critical, High, or Medium findings, including R-01,
    R-05, R-06, R-08, atomicity, cross-incident isolation, prohibited capability
    scans, and regression.
25. README, architecture/contracts and implemented schema notes, requirements
    traceability, progress, pending, ST-05 evidence, story checklist, and actual
    File List are current; the diff stays entirely inside this project, the version
    advances according to project policy, one local Increment-5-only commit is
    created, no remote/push occurs, the worktree is clean, and no Increment 6/7/8
    functionality is introduced by this commit.

## Tasks / Subtasks

- [x] Verify the clean `main` checkpoint at version 0.4.0, commit
  `7be7b77917eaa6f3b2f3089b9446b91a24f91149`, 192 passed/1 conditional skip,
  no remote, and no Increment 5 implementation. (AC: 23, 25)
- [x] Define strict performed-procedure, documentation-revision, and export-
  artifact models and preserve application/port dependency direction. (AC: 1,
  2, 6, 12)
- [x] Add and validate forward-only SQLite migration(s), repositories, and Unit
  of Work operations for immutable performed reports and documentation revisions.
  (AC: 3-5, 10, 11)
- [x] Implement performed-procedure record/list application use cases with exact
  optional action traceability and no execution side effect. (AC: 1-5, 9)
- [x] Implement deterministic nine-section generation exclusively from persisted,
  incident-scoped records and append immutable revisions. (AC: 6-11)
- [x] Implement Markdown and JSON serializers behind `IncidentExporter`, including
  documented schemas and safe hostile-content rendering. (AC: 12-14)
- [x] Implement fixed-root, generated-filename, resolved-containment, collision,
  and atomic-write controls. (AC: 15-18)
- [x] Add CLI human/JSON flows for performed procedures, documentation generation/
  retrieval, and Markdown/JSON export without rules in presentation code. (AC:
  19-21)
- [x] Add unit, contract, real-SQLite integration, CLI, smoke, and security tests;
  cover rollback, isolation, traversal, redaction, invalid data, and prohibited
  capabilities. (AC: 4-5, 7-22)
- [x] Run focused tests and the complete ST-01–04 regression; fix all in-scope
  failures without weakening existing tests. (AC: 22, 23)
- [x] Update README, architecture/schema notes, traceability, progress, pending,
  evidence, checklist, and actual File List. (AC: 23, 25)
- [x] Obtain independent `@qa` functionality/security PASS and resolve every
  Critical, High, or Medium finding before completion. (AC: 24)
- [x] Run final build/install, CLI demonstrations, diff/status/isolation/secret
  checks, create the local Increment 5 commit, confirm a clean worktree, and hand
  off the green gate for Increment 6. (AC: 20, 23-25)

## Dependencies

- ST-01, ST-02, ST-03, and ST-04 are Done; expected baseline is version 0.4.0,
  commit `7be7b77917eaa6f3b2f3089b9446b91a24f91149`, and 192 passing tests plus one
  documented Windows symlink skip.
- ADR-001 requires the modular monolith and inward dependencies; ADR-002 requires
  complete CLI operation before UI; ADR-003 excludes deleted incidents from
  normal exports; ADR-007 forbids execution and makes approval record-only;
  ADR-008 requires isolation and incremental gates.
- Existing `IncidentRepository`, `AnalysisRepository`, `IncidentExporter`,
  `Clock`, `UnitOfWork`, safe-error, configuration, logging, composition-root, and
  CLI human/JSON conventions are the approved boundaries to extend.
- The accepted conceptual schema defines `performed_procedures` and
  `incident_documentation`; implementation must align with the current ST-02/03
  migration/repository conventions and implemented OPEN/CLOSED lifecycle rather
  than infer the broader proposed status model.
- Python 3.12, standard-library SQLite/filesystem/JSON facilities, Pydantic,
  Pytest, Ruff, strict MyPy, and the existing packaging toolchain remain approved.
- User authorization dated 2026-08-02 satisfies the implementation gate for
  Increment 5 and permits a local exclusive commit after QA PASS.

## Planned Tests

| Area | Planned evidence |
|---|---|
| Domain | strict performed report, nine-section documentation, export artifact, invalid/hostile values |
| Persistence | migration order/checksum, FK/constraints, append-only sequence/revision, rollback, concurrency, deleted isolation |
| Separation | suggestions vs performed reports vs approvals, no mutation/execution, exact optional action reference |
| Documentation | all nine ordered sections, persisted sources only, missing optional data, deterministic revisions, cross-incident isolation |
| Markdown | nine headings, Unicode, hostile Markdown/HTML/control text, deterministic content |
| JSON | strict parse, stable schema/key order, Unicode, provenance, round-trip values |
| Filesystem | fixed root, generated names, `..`, absolute/UNC/drive/alternate separators, symlink/resolved escape, collision, atomic failure |
| CLI | record/list, generate/show, Markdown/JSON export, human/JSON parity, safe exit codes, end-to-end persisted journey |
| Security | redaction, SQL/path injection payloads, outside-root non-disclosure, prohibited APIs/capabilities, secret scan |
| Packaging/regression | source and clean-wheel CLI smoke, offline build, full ST-01–04 suite |

All filesystem and SQLite tests use temporary project-contained roots and real
temporary database files. Evidence records command, date, environment, exit code,
test count, and any legitimate conditional skip.

## Dev Notes

- The planned application contracts are `RecordPerformedProcedure`,
  `GenerateIncidentDocumentation`, and `ExportIncident`; commands mutate
  transactionally and queries do not mutate. [Source:
  `docs/architecture/contracts.md#application-use-cases`]
- `IncidentExporter` produces content plus media type and generated filename;
  callers cannot provide paths. [Source:
  `docs/architecture/contracts.md#incidentexporter`]
- The conceptual documentation model requires the approved content and explicitly
  separates suggested from performed procedures. This story makes the suggested
  section explicit in the nine-section output authorized by the user. [Source:
  `docs/architecture/domain-models.md#incidentdocumentation`]
- The conceptual SQLite schema defines incident-bound performed reports and
  unique per-incident documentation revisions. Preserve implemented forward-only,
  checksummed migration and transaction patterns. [Source:
  `docs/architecture/sqlite-schema.md#performed_procedures`;
  `docs/architecture/sqlite-schema.md#incident_documentation`]
- Normal queries and exports exclude logically deleted incidents; audit export is
  outside V1. [Source: `docs/architecture/adr/003-sqlite-audit-soft-delete.md`]
- User-selected paths never reach filesystem APIs; export roots are validated
  configuration. [Source: `docs/architecture/overview.md#security-boundaries`]
- Risk R-01 blocks any executor; R-05 requires fixed roots/generated names/
  containment; R-06 requires export minimization and safe errors; R-08 requires
  consistent deleted filtering. [Source: `docs/security/risk-register.md`]
- G4 requires safe consistent exports and complete earlier regression; G6 fails
  on traversal, shell paths, exposed secrets, automatic actions, or open critical
  findings. [Source: `docs/testing/quality-gates.md`]
- Do not infer proposed `in_progress`, `resolved`, or `reopened` states: the
  implemented lifecycle remains OPEN/CLOSED unless a separately approved story
  changes it. [Source: `docs/architecture/sqlite-schema.md#st-02-implemented-subset`]

### Testing Standards

- Place Pytest coverage under the existing unit, contract, integration, CLI,
  smoke, and security structure; do not remove or weaken existing tests.
- Use real temporary SQLite files for repository/transaction evidence and
  temporary export roots for filesystem evidence; require no internet,
  credentials, real corporate systems, or administrative privileges.
- Ruff and strict MyPy apply to production and test code. Build wheel and sdist
  offline and smoke the installed CLI in a clean project-local environment.
- Record final reproducible results in `docs/testing/evidence/ST-05.md`.

## Risks

- Suggested work may be misreported as performed: keep separate typed commands,
  tables, labels, and sections and test that approval cannot imply execution.
- Generated narrative may fabricate missing facts: assemble only persisted
  sources, explicitly mark unavailable information, and lock deterministic output
  with tests.
- Cross-incident joins may leak data: scope every repository query and revision to
  the requested operational incident and test adversarial identifiers.
- Export traversal or symlink escape may overwrite/disclose files: own the root
  and filename, resolve/contain before write, use atomic creation, and test Windows
  and POSIX-style payloads.
- Exports may expose sensitive incident text: preserve required operational facts
  while excluding secrets/configuration/log internals and documenting the V1
  operator responsibility for incident content.
- Concurrent generation may duplicate revisions: allocate/insert revisions inside
  the established immediate transaction pattern and test collision rollback.
- Scope pressure may pull Streamlit, dashboard, Ollama, or hardening work forward:
  AC 25 and final prohibited-capability/isolation reviews block that drift.

## Quality Gates

1. Pre-development: status remains Approved; models, persistence, nine-section
   mapping, export schema, filename/root policy, and planned tests are traceable.
2. CLI First: record/list/generate/show/export journeys work through application
   services before any Streamlit work begins.
3. Auditability: suggestions and performed reports remain distinct; records and
   revisions are immutable, ordered, transactional, and incident-scoped.
4. Export safety: Markdown and strict JSON are deterministic; filenames are
   generated; containment/traversal/symlink/collision/atomic failure tests pass.
5. Security: no execution, network, LLM, UI, disclosure, cross-incident leakage,
   or unsafe filesystem capability; zero open Critical/High/Medium findings.
6. Regression: Ruff, strict MyPy, complete Pytest, offline build/install smoke,
   CLI E2E, and `git diff --check` pass without weakening ST-01–04.
7. Completion: docs/evidence/checklists/File List/version are current; local
   Increment-5-only commit exists; status is clean; no remote/push; Increment 6
   may proceed only after this gate is recorded green.

## CodeRabbit Integration

> **CodeRabbit Integration**: Disabled
>
> No enabled `coderabbit_integration` key exists in `.aiox-core/core-config.yaml`.
> Use independent `@qa` review plus automated gates. Review focus: persisted-only
> generation, suggestion/performed separation, transaction/revision integrity,
> cross-incident isolation, Markdown/JSON correctness, fixed-root containment,
> atomic writes, safe errors, regression, and prohibited capabilities.

## Definition of Done

- [x] All 25 acceptance criteria have implementation and reproducible evidence.
- [x] All tasks are checked and the actual File List is exact.
- [x] Performed procedures are persisted, immutable, traceable, and demonstrably
  distinct from suggestions/approvals without execution behavior.
- [x] Nine-section documentation is generated and revisioned only from persisted
  incident-scoped records.
- [x] Markdown and JSON exports pass format, containment, traversal, collision,
  atomicity, redaction, and installed-package demonstrations.
- [x] Full quality/build/regression evidence includes commands and exit codes.
- [x] Independent `@qa` verdict is PASS with zero open Critical/High/Medium
  findings.
- [x] Documentation and ST-05 evidence are current.
- [x] One local Increment-5-only commit exists; worktree is clean; no remote or
  push occurred; no Increment 6/7/8 functionality was introduced.

## File List

- `.env.example`
- `README.md`
- `docs/architecture/contracts.md`
- `docs/architecture/sqlite-schema.md`
- `docs/pending.md`
- `docs/progress.md`
- `docs/stories/ST-05-incident-documentation-exports.md`
- `docs/testing/evidence/ST-05.md`
- `docs/testing/requirements-traceability.md`
- `src/supportops/__init__.py`
- `src/supportops/bootstrap.py`
- `src/supportops/cli.py`
- `src/supportops/config.py`
- `src/supportops/contracts.py`
- `src/supportops/documentation_service.py`
- `src/supportops/domain/documentation.py`
- `src/supportops/exporters.py`
- `src/supportops/persistence/migrations.py`
- `src/supportops/repositories.py`
- `tests/cli/test_cli.py`
- `tests/cli/test_documentation_cli.py`
- `tests/integration/test_documentation_persistence.py`
- `tests/integration/test_migrations.py`
- `tests/security/test_export_safety.py`
- `tests/smoke/test_startup.py`
- `tests/unit/test_documentation_exporters.py`

## Dev Agent Record

### Agent Model Used

Codex GPT-5.4 — `@dev` (Dex), autonomous implementation mode.

### Debug Log References

- Initial regression after the first slice found only stale 0.4.0/migration 2
  assertions; updated for version 0.5.0 and migration 3.
- Initial isolated wheel smoke intentionally used `--no-deps` and reported the
  missing runtime dependency; repeated successfully with offline cached deps.

### Completion Notes

- Added immutable performed-procedure and nine-section revision models, migration
  3, append-only SQLite adapters, and persisted-only generation.
- Added replaceable Markdown/JSON exporters and fixed-root contained atomic writer
  with opaque generated names and collision refusal.
- Added CLI-first performed/document/export human and JSON workflows. No UI,
  network, LLM, shell, administrative execution, or later-increment capability.
- Resolved QA findings for failure-path temporary cleanup, Markdown
  literalization, ancestor reparse containment, persisted-corruption translation,
  strict UTC/output invariants, and human/JSON provenance parity.

### Quality Gate Results

- Ruff PASS; strict MyPy PASS (53 files); Pytest PASS (218 passed, 2 conditional
  Windows symlink skips); offline wheel/sdist build PASS; clean-wheel CLI journey
  PASS; `git diff --check` PASS. All commands exited 0.

### Evidence References

- `tests/unit/test_documentation_exporters.py`
- `tests/integration/test_documentation_persistence.py`
- `tests/cli/test_documentation_cli.py`
- `tests/security/test_export_safety.py`
- `docs/testing/evidence/ST-05.md`

## QA Results

### Gate: PASS

- Acceptance criteria: 25/25 after completion administration.
- Final gates: Ruff PASS; strict MyPy PASS across 53 files; Pytest 218 passed,
  2 environment-conditioned symlink skips; offline build/install and CLI E2E PASS;
  `git diff --check` PASS.
- Independent adversarial review covered strict output references/UTC, corrupted
  persisted rows, rollback, cross-incident/deleted isolation, exact nine sections,
  hostile Markdown, strict JSON, ancestor reparse containment, collision,
  temporary cleanup, human/JSON provenance, and both export formats.
- All eight Medium findings raised across review rounds were corrected and closed.
- Final security state: zero open Critical, High, or Medium findings; no executor,
  shell, network, LLM, UI, or later-increment capability introduced.

Verdict recorded by `@qa` — Quinn on 2026-08-02. Status: `Approved → Done`.

## Change Log

| Date | Version | Description | Author |
|---|---:|---|---|
| 2026-08-02 | 0.1.0 | Initial ST-05 derived from the authorized Increment 5 scope, accepted architecture, ADRs, and completed ST-01–04 baseline; Status: Approved | @sm — River |
| 2026-08-02 | 0.2.0 | Complete ST-05 implementation/test slice at application 0.5.0; 205 passed, 1 conditional skip; awaiting independent QA/final administration | @dev — Dex |
| 2026-08-02 | 0.3.0 | Resolved five QA Medium findings plus CLI provenance parity; 211 passed, 2 conditional symlink skips; ready for QA re-review | @dev — Dex |
| 2026-08-02 | 0.4.0 | Closed residual strict-reference and typed-corruption findings; independent QA PASS; 218 passed, 2 skips | @dev — Dex / @qa — Quinn |
