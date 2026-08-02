# ST-03 — Deterministic Triage and Evidence Collection

## Status

**Done**

Explicit human approval for ST-03 and Increment 3 was received on 2026-08-01.
Implementation is complete and the story is in independent QA review. Increment 4
remains unauthorized and has not started.

### Approval Evidence

- Approved by: project user through the active AIOX orchestration.
- Approved scope: ST-03 deterministic triage and evidence collection as written.
- Transition: `Draft → Ready`.
- Date: 2026-08-01.
- Boundary preserved: documentation-only transition; no code, commit, remote or
  push operation authorized by this record.

## Objective

Implement the approved local, versioned triage policy through application services and CLI-first flows. The system must assess supported impact and urgency evidence, map all 16 combinations to P1-P4, recommend N1/N2, retain escalation reasons, identify evidence gaps, ask non-duplicated diagnostic questions, stop safely when required, and persist immutable triage snapshots with the exact policy revision.

## Story

**As a** support professional working on an existing incident,
**I want** deterministic, version-traceable triage and evidence-gap questions,
**so that** priority, support ownership, escalation and stopping decisions are consistent, explainable and never fabricated from incomplete information.

## Executor Assignment

```yaml
executor: "@dev"
quality_gate: "@qa"
quality_gate_tools: [Ruff, MyPy, Pytest, manual-security-review]
```

## Scope

### In scope

- One project-owned policy artifact implementing policy `supportops-triage`, schema version `1`, the four impact values, four urgency values and P1-P4.
- Strict loading and startup validation with `fallback_behavior: fail_closed`.
- Exactly 16 unique rules `MX-LL` through `MX-CC`, with rationale and baseline routing.
- Deterministic impact, urgency, priority, ranked N1/N2/incident-coordination
  routing, escalation and `stop` evaluation.
- Evidence-gap questions `DQ-01` through `DQ-12`, without repeating answered facts.
- Structured risk assessment using a closed catalog; no risk inference from text.
- Immutable SQLite triage snapshots and questions linked to operational incidents.
- Exact policy/schema/matrix version and checksum or equivalent immutable revision on every result.
- Re-triage as an appended snapshot, never overwrite.
- Stable CLI human-readable and machine-readable JSON output.
- Unit, contract, real-SQLite integration, CLI, security, smoke and regression tests.

### Out of scope

- Streamlit/UI, runbooks, knowledge search, hypotheses and troubleshooting plans.
- Command suggestions, action execution or changes to human approvals.
- Ollama/OpenAI/LLMs, HTTP or any network client.
- Category/subcategory inference not defined by the policy.
- SLA promises, incident lifecycle mutation, restore or physical deletion.
- Policy reload during a running operation.
- Shell, subprocess, dynamic execution or external commands.

## Rules

1. Impact and urgency are independent and each requires supporting evidence. Title, requester role, pressure or category alone never sets priority.
2. The highest supported criteria win. Unknown, unsupported or contradictory dimensions return `triage_incomplete`.
3. P1 is only critical/critical. Any high or critical dimension yields at least P2. P4 is only low/low.
4. Priority never authorizes an action, grants privilege, promises an SLA or executes a command.
5. Escalation is additive; routes are strictly ordered
   `N1 < N2 < incident_coordination`, each `ESC-*` declares a destination, all
   reasons are retained, and the highest matched route wins without lowering priority.
6. N1 is recommended only when all five policy conditions hold; otherwise the matrix route or escalation recommends N2.
7. Questions derive only from absent or contradictory facts; answered questions are not repeated. Risk uses the closed catalog and structured status defined by the policy, never inference from free text.
8. Blocking questions precede downstream content. This story generates no solution, hypothesis or plan.
9. `STOP-01..07` returns a structured stop, preserves evidence and recommends escalation without lifecycle, approval or execution side effects.
10. Unknown or logically deleted incidents cannot be operationally triaged.
11. Results and questions are immutable; re-triage appends a new snapshot.
12. Invalid, missing, duplicate, contradictory, unreadable or unsupported policy configuration fails closed with a safe error.
13. Errors/logs omit incident payloads, tokens, policy contents, SQL, absolute paths and tracebacks.

## Acceptance Criteria

1. The policy artifact declares policy ID, schema/matrix versions, effective date, exact allowed enums and `fallback_behavior: fail_closed`.
2. It contains exactly 16 Cartesian rules with stable unique IDs, rationale, priority and routing.
3. A valid policy loads offline and exposes a deterministic checksum or immutable revision.
4. Missing/duplicate rules, unknown enums, unsupported versions, malformed/unreadable content, contradictory P1 mapping or non-fail-closed fallback cause safe startup failure with no silent fallback.
5. Each impact level requires its documented minimum evidence; highest supported impact wins and requester identity alone does not raise it.
6. Each urgency level requires its documented minimum evidence; urgency wording alone does not raise it.
7. All 16 cells return the exact approved priority and rule ID.
8. P1 occurs only for critical/critical; a high or critical dimension never returns P3/P4.
9. Repeated evaluation of the same normalized evidence and policy revision is identical offline.
10. A complete result contains policy/schema/matrix/revision traceability, normalized inputs, rule, rationale, dimensions, priority, support level, escalation and generation time.
11. `ESC-01..06` independently produce their documented explicit destination;
    simultaneous reasons are retained, `N1 < N2 < incident_coordination` is
    enforced, the highest route wins, and escalation cannot reduce priority.
12. Conditional escalation follows the four documented triggers: `MX-LH` and
    `MX-MM` route N1 to N2, while baseline-N2 `MX-MH` routes to
    `incident_coordination`, without bypassing mandatory triggers.
13. N1 requires all five N1 conditions; each prohibited condition routes N2 while safe evidence intake remains non-executing.
14. N1/N2 recommendation creates no approval, execution capability or lifecycle mutation.
15. `DQ-01..12` are generated under documented conditions with topic, question,
    required evidence, reason and blocking flag; `DQ-10` depends only on the
    structured risk status and closed risk-signal catalog, never free text.
16. Answered evidence is not requested again; contradictions produce questions rather than inferred answers.
17. Incomplete/unsupported/contradictory evidence returns `triage_incomplete` without priority, support level or solution.
18. Blocking questions precede downstream markers in both CLI output formats.
19. `STOP-01..07` each returns a structured stop with evidence, matched reason and
    escalation path; risk stop/escalation requires a valid structured
    `suspected`/`confirmed` status and catalog ID.
20. Stop precedes plan content and does not mutate incident lifecycle, record approval or execute an action.
21. A persisted, non-deleted incident with sufficient evidence is triaged by CLI with stable output and exit 0.
22. Machine-readable output is valid JSON with full rule and revision traceability.
23. Unknown/deleted incidents return the existing safe not-found behavior.
24. Result and questions persist atomically in real SQLite and round-trip without loss.
25. Re-triage creates a new immutable snapshot without updating/deleting prior snapshots/questions.
26. Persistence uses FK, constraints, UoW and parameterized SQL; injected failure rolls back partial triage writes.
27. Hostile incident text remains data and cannot change policy, rule selection, SQL or CLI flow.
28. Errors/logs redact sensitive incident text, tokens, configuration contents, SQL, paths and tracebacks.
29. No shell/executor, UI, knowledge, hypotheses/plans, LLM or network capability is introduced.
30. Ruff, strict MyPy, Pytest, build/install, CLI demonstrations, ST-01/ST-02 regression and `git diff --check` pass with evidence.
31. The final diff/File List stay inside this isolated project; no remote or push occurs.

## Tasks

- [x] Record explicit approval before implementation. (AC: 31)
- [x] Add and validate the project-owned policy with matrix, escalation, gap and stop rules. (AC: 1-4)
- [x] Extend typed domain contracts for evidence, immutable result/question, escalation and stop outcomes. (AC: 5-20, 29)
- [x] Implement deterministic policy loading/evaluation without fallback. (AC: 3-20)
- [x] Add an ordered checksummed SQLite migration for immutable snapshots/questions. (AC: 24-26)
- [x] Implement analysis repositories and transactional services; reject deleted/unknown incidents and append re-triage. (AC: 23-26)
- [x] Extend composition root and CLI; keep SQL/domain decisions out of CLI. (AC: 18, 21-23)
- [x] Implement canonical `T3-CFG`, `T3-IMP`, `T3-URG`, `T3-MX`, `T3-PRI`, `T3-ESC` and `T3-LVL` tests. (AC: 1-14)
- [x] Implement `T3-DQ`, `T3-RISK`, `T3-GAP` and `T3-STOP` tests. (AC: 15-20)
- [x] Add real-SQLite round-trip, append-only, FK and fault-rollback tests. (AC: 23-26)
- [x] Add CLI, hostile input, redaction, offline/prohibited capability and full regression tests. (AC: 21-30)
- [x] Update README, architecture subset notes, traceability, progress, pending, evidence and actual File List. (AC: 30-31)
- [x] Run all gates, fix failures and request independent QA before Done. (AC: 30-31)


## Dependencies

- ST-01 accepted; ST-02 is `Done` with 26/26 AC and a 41-test baseline.
- `docs/support/triage-policy-v1.md` is the operational source proposed for this increment.
- Reuse existing Impact/Urgency/Priority, Settings, composition-root, migration, repository, UoW, safe-error and logging patterns.
- Python 3.12, Pydantic/Pydantic Settings, standard-library SQLite and Pytest remain the approved stack.
- Explicit human approval is required before implementation.

## Planned Tests

| Area | Canonical IDs |
|---|---|
| Policy configuration | `T3-CFG-01..11` |
| Impact and urgency | `T3-IMP-01..05`, `T3-URG-01..05` |
| Matrix and invariants | `T3-MX-01..16`, `T3-PRI-01..04` |
| Escalation and level | `T3-ESC-01..13`, `T3-LVL-01..04` |
| Questions, structured risk and gaps | `T3-DQ-01..12`, `T3-RISK-01..06`, `T3-GAP-01..06` |
| Stop outcomes | `T3-STOP-01..09` |
| CLI | `T3-CLI-01..04` |
| SQLite | `T3-INT-01..02` plus FK/fault rollback |
| Security/offline | `T3-SEC-01..03` |
| Regression | `T3-REG-01` |

Integration completion requires real temporary SQLite. Evidence records command, date, environment, exit code and counts.

## Risks

- Hidden fallback or policy drift makes priority untraceable: fail closed and persist exact revision.
- Missing evidence can be mistaken for low severity: block priority/support output when dimensions lack support.
- P1/P2 boundary regressions: test every cell and invariant independently.
- Escalation/stop ordering can be bypassed: evaluate additively and retain all reasons.
- Ambiguous route precedence can leave baseline N2 without a real escalation:
  enforce the total route order and explicit destinations, including MX-MH to
  incident coordination on a conditional trigger.
- Free-text risk inference can be unstable or attacker-controlled: accept only
  validated structured status and closed-catalog IDs.
- Re-triage can overwrite audit history: require append-only snapshots and fault rollback tests.
- Hostile incident text can influence parsing or leak: treat it as data and test canaries/redaction.
- N1/N2 can be mistaken for authorization: never create approval token, privilege, action or executor.
- Scope pressure can pull UI/runbooks/hypotheses/plans/LLM into this increment: prohibited capability scans block completion.

## Quality Gates

1. Pre-development: remain Draft until human approval; policy and test IDs are consistent.
2. Policy: configuration, all 16 cells and boundary tests pass; no fallback exists.
3. Safety: incomplete evidence, escalation and stop tests pass without authorization/execution.
4. Persistence: real SQLite round-trip, append-only, FK, parameterization and fault rollback pass.
5. CLI First: journeys work through CLI; CLI contains no SQL or policy decisions.
6. Security: hostile inputs, redaction, offline and prohibited-capability scans pass with zero Critical/High.
7. Completion: Ruff, MyPy, Pytest, build/install, CLI, regressions and diff check pass; documentation/File List/evidence are current.

## CodeRabbit Integration

> **Disabled:** no enabled `coderabbit_integration` key exists in the loaded `core-config.yaml`. Use independent manual review plus automated gates; record unavailability as such.

Review assignment: `@dev` implements, Support Specialist validates policy content, and `@qa` owns the independent gate. Focus on matrix completeness, evidence sufficiency, escalation/stop precedence, immutable SQLite persistence, safe errors and scope exclusions.

## Definition of Done

- [x] Implementation approval recorded.
- [x] Every AC maps to a test/evidence item; no component is complete without its test.
- [x] All applicable canonical `T3-*` tests pass.
- [x] Valid/invalid policy behavior and all 16 cells are demonstrated without fallback.
- [x] Gap, structured-risk, ranked routing, escalation and stop flows pass without side effects.
- [x] CLI human/JSON and deleted/unknown behavior pass.
- [x] Real SQLite snapshot, re-triage, FK and rollback tests pass.
- [x] ST-01/ST-02 regression and all gates pass with exit codes recorded.
- [x] Security review has zero open Critical/High.
- [x] README, architecture, traceability, progress, pending, evidence and actual File List are current.
- [x] Independent QA issues PASS before Done.


## Dev Notes

- Reuse application services/composition root; CLI has no policy rules or SQL. [Source: `docs/architecture/contracts.md#cli-contract`]
- Implement the validated `PriorityPolicy` boundary with safe fail-closed errors. [Source: `docs/architecture/contracts.md#prioritypolicy`]
- Persist immutable results/questions through `AnalysisRepository`; normal access excludes soft-deleted incidents. [Source: `docs/architecture/contracts.md#analysisrepository`]
- Use the documented `TriageResult` and `DiagnosticQuestion` fields. [Source: `docs/architecture/domain-models.md#triageresult`; `docs/architecture/domain-models.md#diagnosticquestion`]
- Matrix, evidence, routing, escalation, stop rules and canonical tests come from `docs/support/triage-policy-v1.md`.
- Reuse ST-02 checksummed migrations, FK/timeout, explicit UoW, sequencing, safe errors and real-SQLite patterns. [Source: `docs/stories/ST-02-sqlite-incident-lifecycle.md#completion-notes`]
- Increment 3 is CLI-first and precedes knowledge, export, Streamlit and LLM work. [Source: `docs/implementation-plan.md#increment-3--deterministic-triage-and-evidence`]

### Testing standards

- Pytest; real temporary SQLite for integration evidence; Ruff and strict MyPy.
- Preserve the full 41-test ST-01/ST-02 baseline.
- Use injectable clock/ID boundaries where determinism matters.
- Mandatory smoke remains offline; manually inspect execution APIs, SQL bindings, redaction and scope.
- Record results in `docs/testing/evidence/ST-03.md`.

## File List

- `.env.example`
- `README.md`
- `docs/architecture/contracts.md`
- `docs/architecture/domain-models.md`
- `docs/architecture/sqlite-schema.md`
- `docs/pending.md`
- `docs/progress.md`
- `docs/stories/ST-03-deterministic-triage-evidence.md`
- `docs/support/triage-policy-v1.md`
- `docs/testing/evidence/ST-03.md`
- `docs/testing/requirements-traceability.md`
- `pyproject.toml`
- `src/supportops/__init__.py`
- `src/supportops/bootstrap.py`
- `src/supportops/cli.py`
- `src/supportops/config.py`
- `src/supportops/domain/triage.py`
- `src/supportops/persistence/migrations.py`
- `src/supportops/policies/triage-v1.json`
- `src/supportops/repositories.py`
- `src/supportops/triage_engine.py`
- `src/supportops/triage_policy.py`
- `src/supportops/triage_service.py`
- `tests/cli/test_cli.py`
- `tests/cli/test_triage_cli.py`
- `tests/contract/test_triage_policy.py`
- `tests/integration/test_migrations.py`
- `tests/integration/test_triage_persistence.py`
- `tests/security/test_triage_safety.py`
- `tests/smoke/test_startup.py`
- `tests/unit/test_triage_engine.py`

## Dev Agent Record

### Agent Model Used

OpenAI Codex (GPT-5)

### Started At

2026-08-01

### Completed At

2026-08-01

### Implementation Notes

- Added one packaged, versioned, fail-closed JSON policy with exact matrix,
  evidence criteria, escalation, questions, risk and stop metadata.
- Implemented immutable typed triage input/output, deterministic evaluation,
  application service, composition-root wiring and CLI `triage run/history`.
- Added checksummed migration 2 and append-only per-incident snapshots inside the
  existing explicit SQLite Unit of Work.
- Preserved incomplete-state safety: no priority or route is fabricated when
  criteria contradict, boundary evidence is missing or a blocking question exists.
- Kept Streamlit, knowledge/runbook search, hypotheses, plans, LLM/network and
  command execution outside the increment.

### Debug Log References

- Initial QA identified conditional-escalation traceability and stale version
  expectations; both were corrected with focused tests.
- Follow-up QA identified unsupported dimension derivation, missing diagnostic
  questions, blocking-question precedence and MX-HC/MX-CC boundary gaps; each was
  corrected before the final regression.
- The Windows sandbox helper intermittently returned
  `CreateProcessWithLogonW failed: 2`; localized PowerShell document writes were
  used only after the required `apply_patch` helper also failed. No application
  code was changed by the documentation fallback.
- The unavailable `py -3.12` launcher probe was replaced by the verified project
  Python 3.12.12 interpreter for the clean-wheel smoke test.

### Completion Notes

All 31 acceptance criteria have corresponding implementation tests or recorded
validation evidence. The deterministic policy remains an initial, calibratable V1;
its P2 concentration is explicitly documented as a conservative project decision,
not a universal ITSM standard. The story is ready for independent QA and remains
`InReview`, never `Done`, until that gate records PASS.

### Quality Gate Results

- Baseline before ST-03: 41/41 tests passed, exit 0.
- Focused policy/engine suite: 95/95 tests passed, exit 0.
- Full ST-01/ST-02/ST-03 regression: 150/150 tests passed, exit 0.
- Ruff: PASS, exit 0.
- Strict MyPy: PASS across 37 source files, exit 0.
- Wheel and sdist 0.3.0 build: PASS, exit 0.
- Clean wheel install, CLI version and configuration validation: PASS, exit 0.
- `git diff --check`: PASS, exit 0.

### Evidence References

- `docs/testing/evidence/ST-03.md`

### Actual File List

The authoritative 31-file list is recorded in this story's `File List` section.

## QA Results

### Gate: PASS

- Acceptance criteria: 31/31 verified through implementation, tests, and recorded
  evidence.
- Independent gates: Ruff PASS; strict MyPy PASS across 37 source files; full
  Pytest regression 150/150; focused ST-03 suite 108/108; wheel/sdist build PASS;
  `git diff --check` PASS.
- Real SQLite/CLI journey: migration 2, complete P2/N2 triage, incomplete triage
  with blocking questions and STOP-04, P1 incident coordination, and immutable
  append-only snapshot sequences 1/2/3 verified.
- Security: zero open Critical, High, or Medium findings; no shell/executor,
  network, UI, LLM, or automatic action capability introduced.
- QA-raised issues corrected before PASS: stale version regression, conditional
  escalation traceability, highest-supported dimension derivation, DQ boundary
  conditions, blocking-question safety, MX-HC/MX-CC stop behavior, and patch
  hygiene.
- Residual documented limitations: the initial V1 policy requires future
  operational calibration; supported criteria and actor identity remain
  human-declared; retention and broader sensitive-data guidance remain pending.
- CodeRabbit was unavailable by project configuration; independent manual review
  and automated gates were used.

Verdict recorded by `@qa` — Quinn on 2026-08-01. Status transition:
`InReview → Done`.

## Change Log

| Date | Version | Description | Author |
|---|---:|---|---|
| 2026-08-01 | 0.1.0 | Initial draft derived from approved project artifacts and Support Specialist policy | @sm — River |
| 2026-08-01 | 0.1.1 | Explicit human approval recorded — Status: Draft → Ready | @sm — River |
| 2026-08-01 | 0.2.0 | Development started (autonomous execution) — Status: Ready → InProgress | @dev — Dex |
| 2026-08-01 | 0.3.0 | Implementation and evidence completed — Status: InProgress → InReview | @dev — Dex / @sm — River |
| 2026-08-01 | 0.3.1 | Independent QA PASS — Status: InReview → Done | @qa — Quinn |
