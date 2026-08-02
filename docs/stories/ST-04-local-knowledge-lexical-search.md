# ST-04 — Local knowledge base and deterministic lexical search

## Status

Done

Explicit approval was granted by the user on 2026-08-02 to create and implement
Increment 4 autonomously within `projects/supportops-command-center`. This story
authorizes Increment 4 only; Increment 5 remains blocked.

## Objective

Deliver the approved local Markdown knowledge base and an offline, explainable,
deterministic lexical search through the CLI, while preserving the replaceable
`KnowledgeSearch` boundary and the project's non-executing safety model.

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
**I want** to search a curated local set of operational runbooks using normalized
lexical terms,
**so that** I can find relevant, traceable guidance offline without an LLM,
network service, vector database, or executable administrative action.

## In Scope

- A documented Markdown runbook format with validated metadata: identifier,
  title, aliases, category, symptoms, keywords, risk notes, escalation criteria,
  revision, and content.
- Exactly the five mandatory initial runbooks:
  1. denied access to a shared mailbox in Outlook;
  2. locked user in Active Directory or Entra ID;
  3. OneDrive not synchronizing;
  4. computer without network access;
  5. denied access to a SharePoint folder or library.
- Local search across title, aliases, symptoms, keywords, and content.
- Case- and accent-insensitive normalization, deterministic lexical scoring,
  explicit stable tie-breaking, matched terms, excerpts, and source evidence.
- A concrete local Markdown adapter behind the existing/planned
  `KnowledgeSearch` interface and an application service used by the CLI.
- `supportops knowledge search` output for humans and machine-readable JSON,
  following existing CLI conventions and safe error handling.
- Safe handling of malformed/invalid Markdown and metadata, no-result queries,
  path traversal, symlinks/resolved paths, and files outside the configured
  knowledge root.
- Unit, contract, integration, CLI, security, and full ST-01/ST-02/ST-03
  regression evidence.

## Out of Scope

- Embeddings, vector databases, semantic RAG, OpenAI, Ollama, or any network
  dependency.
- Streamlit or any other UI.
- Hypothesis trees, generated troubleshooting plans, approvals, exports, and
  Increment 5 behavior.
- Shell/process execution, administrative commands, automatic remediation, or
  changes to Microsoft 365, Active Directory, Entra ID, SharePoint, endpoints,
  or network configuration.
- Files outside `projects/supportops-command-center/`, remote configuration,
  push, release, or global software/configuration changes.

## Rules and Safety Invariants

1. Required behavior is fully local and deterministic; identical normalized
   corpus and query produce identical ordered results and evidence.
2. Normalization removes case and accent distinctions without changing source
   files or fabricating semantic equivalence.
3. Only validated regular Markdown files whose resolved paths remain inside the
   configured knowledge root may be indexed or returned.
4. User query text and runbook content are data; neither may alter filesystem
   scope, CLI flow, scoring rules, logging policy, or program behavior.
5. Invalid documents fail safely and cannot poison the valid corpus. Safe output
   identifies an actionable document error without exposing sensitive content,
   full paths, tracebacks, or configuration values.
6. Ranking must be explainable from documented lexical matches. Score inputs,
   field contribution, duplicate-term treatment, ordering, and a total stable
   tie-break rule must be specified and covered by tests before completion.
7. Search results contain validated document metadata, lexical score, matched
   terms, excerpt/evidence, revision, and a root-contained relative source path.
8. Runbook procedures remain human-readable suggestions. No executor port,
   subprocess/shell API, administrative capability, or approval side effect is
   introduced.
9. The CLI delegates parsing/search decisions to application/domain boundaries;
   it does not parse Markdown or implement scoring.
10. Invalid configuration/root conditions fail closed; zero matches is a valid
    successful search, not a fabricated fallback.

## Acceptance Criteria

1. A project-owned specification defines the required Markdown metadata, content
   structure, validation behavior, revision handling, and safe authoring rules.
2. The five mandatory runbooks exist under one configured project-local knowledge
   root, conform to the specification, contain no real credentials or personal
   data, and provide symptoms, safe evidence collection, risks, stop/escalation
   criteria, and non-executing guidance appropriate to their named scenario.
3. A typed `KnowledgeDocument` represents the documented fields and records only
   a root-contained relative source path; a typed `SearchResult` contains document
   metadata, score, matched terms, excerpt/evidence, and revision.
4. The `KnowledgeSearch` interface remains replaceable and independent of CLI and
   Markdown implementation details; the local Markdown adapter implements it.
5. Queries and indexed fields normalize case and accents consistently, including
   Portuguese terms, while results retain original display text.
6. Search evaluates title, aliases, symptoms, keywords, and content and never
   treats an unmatched document as a match.
7. The lexical scoring algorithm, field contributions, term handling, result
   ordering, and stable total tie-break are documented and independently tested.
8. Repeating the same query against the same corpus yields byte-equivalent JSON
   ordering, scores, matched terms, excerpts, revisions, and relative paths.
9. A relevant query can retrieve each of the five runbooks; aliases and symptoms
   are demonstrated as searchable evidence, not only title matches.
10. Human CLI output presents ranked matches with score, matched terms, excerpt,
    revision, and relative source evidence; JSON output exposes the equivalent
    structured result and exits 0.
11. A valid query with no matches returns an explicit empty/no-results response,
    valid empty JSON results, and exit 0 without fallback or invented guidance.
12. Empty or otherwise invalid queries return a safe actionable validation error
    using the established CLI error contract and a non-zero exit code.
13. Missing roots, unreadable files, malformed metadata, unsupported encodings,
    duplicate document IDs, and other invalid corpus content fail safely according
    to the documented validation policy, without unsafe partial or fabricated data.
14. Traversal attempts (`..`, absolute paths, alternate separators), symlink or
    resolved-path escapes, and files outside the allowed root are rejected and
    never indexed, read, disclosed, or returned.
15. Hostile query/Markdown text remains inert data and cannot invoke SQL, shell,
    subprocess, network, dynamic import, template execution, or administrative
    behavior.
16. Errors and logs redact sensitive runbook/query content, secrets, configuration
    values, absolute paths, and tracebacks, consistent with existing safe-error
    and logging behavior.
17. No embeddings, vector/RAG stack, LLM/provider, Streamlit/UI, network client,
    shell/executor, hypothesis/plan generation, export, or Increment 5 capability
    is introduced.
18. Ruff, strict MyPy, Pytest, package build/install smoke, CLI demonstrations,
    `git diff --check`, and the complete ST-01/ST-02/ST-03 regression pass with
    commands, dates, environment, exit codes, and counts recorded.
19. Independent `@qa` review verifies functionality and security with zero open
    Critical/High findings, including traversal, corpus validation, deterministic
    ranking/ties, no-result behavior, prohibited capability scans, and scope.
20. README, architecture/contract notes, requirements traceability, progress,
    pending items, ST-04 evidence, story checklist, and actual File List are
    current; the final diff stays entirely inside this project, a local ST-04-only
    commit is created, no remote/push occurs, and work stops before Increment 5.

## Tasks / Subtasks

- [x] Confirm the expected clean checkpoint, 0.3.0 version, 150-test baseline,
  `main`, commit `8dbf4d6f41b594b848dad7f53096ed546fe6f72b`, and no remote. (AC: 18, 20)
- [x] Define and validate the Markdown runbook format and safe corpus policy.
  (AC: 1, 3, 13, 16)
- [x] Author and review all five mandatory runbooks. (AC: 2, 9)
- [x] Add typed knowledge models and preserve the `KnowledgeSearch` port. (AC: 3, 4)
- [x] Implement the root-contained Markdown loader and invalid-content handling.
  (AC: 13-16)
- [x] Implement case/accent normalization, field matching, explainable scoring,
  excerpt evidence, ordering, and total deterministic tie-breaking. (AC: 5-9)
- [x] Add the application service and `knowledge search` human/JSON CLI journey
  without parser/scoring logic in the CLI. (AC: 4, 10-12)
- [x] Add unit and contract tests for models, normalization, all searchable fields,
  ranking, ties, repeatability, excerpts, and no results. (AC: 3-9, 11)
- [x] Add integration/CLI tests for all five files, invalid corpus/query behavior,
  human/JSON output, and package inclusion/installation. (AC: 2, 9-13, 18)
- [x] Add security tests for traversal, resolved-path/symlink escape where supported,
  outside-root files, hostile content, redaction, and prohibited capabilities.
  (AC: 14-17)
- [x] Run focused tests and the complete 150-test baseline regression; fix all
  in-scope failures. (AC: 18)
- [x] Update README, architecture/contracts, traceability, progress, pending,
  evidence, checklist, and actual File List. (AC: 18, 20)
- [x] Obtain independent `@qa` functional/security PASS and resolve findings.
  (AC: 19)
- [x] Run final diff/status/isolation checks, create the local Increment 4 commit,
  and stop before Increment 5. (AC: 20)

## Dependencies

- ST-01, ST-02, and ST-03 are `Done`; their complete baseline is 150 passing tests.
- Current expected package version is 0.3.0 and the expected starting commit is
  `8dbf4d6f41b594b848dad7f53096ed546fe6f72b` on clean `main` with no remote.
- ADR-005 is accepted and requires local lexical Markdown search behind
  `KnowledgeSearch`.
- Reuse existing settings, composition-root, CLI human/JSON, safe errors,
  structured redacted logging, deterministic boundaries, and test patterns.
- Python 3.12, standard-library filesystem/text facilities, Pydantic stack,
  Pytest, Ruff, strict MyPy, and setuptools remain the approved stack.
- User approval dated 2026-08-02 satisfies the implementation gate for Increment 4.

## Planned Tests

| Area | Planned evidence |
|---|---|
| Runbook contract | required metadata/sections; all five valid; duplicate IDs; malformed metadata; encoding/read failure |
| Normalization | case and accent equivalence; original display text retained; empty/invalid query |
| Search fields | independent title, alias, symptom, keyword, and content matches |
| Ranking | score contribution, multiple matches, stable tie-break, repeated byte-equivalent JSON |
| Results | matched terms, excerpt, revision, relative path; unmatched excluded; explicit empty results |
| CLI | human and JSON matches, every runbook retrievable, validation errors and exit codes |
| Filesystem security | `..`, absolute/alternate paths, outside-root file, resolved/symlink escape, no path disclosure |
| Content security | hostile query/Markdown inert, safe errors/redaction, prohibited APIs/capabilities absent |
| Packaging/integration | installed package can discover approved runbooks locally and offline |
| Regression | full ST-01/ST-02/ST-03 suite plus all ST-04 tests |

Integration evidence must use temporary project-contained knowledge roots where
isolation behavior is under test. Completion evidence records command, date,
environment, exit code, and test count.

## Dev Notes

- ADR-005 fixes the approach: versioned local Markdown, validated metadata,
  aliases, normalization, term matching, deterministic scoring, and no embeddings
  or provider dependency. [Source: `docs/architecture/adr/005-lexical-knowledge.md`]
- `KnowledgeSearch` accepts a plain query and returns ranked results only from
  validated files inside the configured knowledge directory. Keep the interface
  independent of the concrete Markdown adapter. [Source:
  `docs/architecture/contracts.md#knowledgesearch`]
- Planned `KnowledgeDocument` fields are `id`, `title`, `aliases`, `category`,
  `symptoms`, `risk_notes`, `escalation_criteria`, root-contained path, content,
  and revision; this increment adds the explicitly authorized `keywords` metadata.
  Search results carry metadata, lexical score, matched terms, and excerpt.
  [Source: `docs/architecture/domain-models.md#knowledgedocument-and-searchresult`]
- The dependency direction is CLI -> application service -> port/domain, with
  Markdown search as infrastructure. User-selected paths must never directly
  reach filesystem APIs. [Source: `docs/architecture/overview.md#logical-view`;
  `docs/architecture/overview.md#security-boundaries`]
- Risk R-05 requires fixed roots and containment checks; R-10 accepts the V1
  synonym limitation and mitigates it with aliases/tags and explainable score.
  [Source: `docs/security/risk-register.md`]
- Quality Gate G3 requires the five runbooks to be found while commands remain
  suggestions. G6 fails on effective traversal, arbitrary shell paths, exposed
  secrets, automatic sensitive actions, or open critical findings. [Source:
  `docs/testing/quality-gates.md#g3--knowledge-and-deterministic-analysis`;
  `docs/testing/quality-gates.md#g6--security`]
- Existing traceability identifies canonical knowledge cases for all five files,
  normalized search, corrupt content, and traversal; ST-04 implementation should
  update the current story mapping without deleting the requirement. [Source:
  `docs/testing/requirements-traceability.md#requirements--stories--tests`]
- ST-03 completed at 150/150 and preserved safe human/JSON CLI, redaction,
  deterministic processing, offline behavior, and prohibited-capability scans.
  Reuse those patterns and keep triage behavior unchanged. [Source:
  `docs/stories/ST-03-deterministic-triage-evidence.md#quality-gate-results`]
- No new environment variables are required unless the existing validated settings
  pattern needs a project-local knowledge-root setting. If added, it must default
  safely inside the project/package boundary and be documented without real paths.

### Testing Standards

- Pytest with unit, contract, integration, CLI, smoke, and security placement
  matching the existing `tests/` structure.
- Ruff and strict MyPy apply to all production code; build both wheel and sdist and
  perform a clean installed-CLI smoke where supported by the existing evidence flow.
- Keep the complete 150-test ST-01/ST-02/ST-03 baseline green.
- Filesystem tests use temporary roots and never depend on internet, credentials,
  real corporate systems, or administrative privileges.
- Record final results in `docs/testing/evidence/ST-04.md`.

## Risks

- Lexical search can miss unlisted synonyms: curated aliases/keywords and an
  explainable score mitigate but do not eliminate this accepted V1 limitation.
- Weighting can appear arbitrary or drift: document every scoring contribution
  and lock ranking/ties with contract tests.
- Invalid files can make results partial and misleading: apply one documented,
  tested fail-safe corpus policy and never fabricate fallback results.
- Traversal or resolved-path escape can disclose local files: resolve and contain
  every candidate beneath the fixed root before reading or returning it.
- Operational text can be mistaken for executable authorization: keep runbooks as
  content only and retain negative API/capability scans.
- Packaging can omit Markdown assets: verify built/installed behavior, not only
  source-tree execution.
- Scope pressure can pull hypotheses/plans/UI/LLM into this increment: AC 17 and
  final isolation review block those additions.

## Quality Gates

1. Pre-development: story remains `Approved`; format, score/tie specification,
   roots, and tests are traceable before completion.
2. Content: all five runbooks validate and are independently retrievable.
3. Determinism: normalization, ranking, ties, evidence, and repeated JSON pass.
4. CLI First: human and JSON search/no-result journeys work without UI or network.
5. Security: malformed content, traversal/resolved escape, hostile text, redaction,
   and prohibited capability tests pass with zero Critical/High findings.
6. Regression: Ruff, strict MyPy, Pytest, build/install, CLI demonstrations, prior
   150-test baseline, and `git diff --check` pass.
7. Completion: documentation, evidence, checklist, actual File List, diff/status,
   and local commit are current; no remote/push and no Increment 5 work.

## CodeRabbit Integration

> **CodeRabbit Integration**: Disabled
>
> No enabled `coderabbit_integration` key exists in `.aiox-core/core-config.yaml`.
> Use independent `@qa` review plus automated gates. Review focus: deterministic
> score/ties, filesystem containment, invalid corpus behavior, redaction, CLI
> boundary, packaging, regression, and prohibited capabilities.

## Definition of Done

- [x] All 20 acceptance criteria have implementation or recorded evidence.
- [x] All tasks and subtasks are checked and the actual File List is exact.
- [x] Five validated runbooks and deterministic CLI search/no-result journeys pass.
- [x] Invalid content and filesystem/security cases pass without disclosure or
  side effects.
- [x] Full quality/build/regression evidence includes commands and exit codes.
- [x] Independent `@qa` verdict is PASS with zero open Critical/High findings.
- [x] Documentation and ST-04 evidence are current.
- [x] A local Increment 4-only commit exists; status/diff are reported; no remote,
  push, or Increment 5 work occurs.

## File List

- `README.md`
- `docs/architecture/contracts.md`
- `docs/architecture/domain-models.md`
- `docs/pending.md`
- `docs/progress.md`
- `docs/stories/ST-04-local-knowledge-lexical-search.md`
- `docs/support/knowledge-runbook-format.md`
- `docs/testing/evidence/ST-04.md`
- `docs/testing/requirements-traceability.md`
- `pyproject.toml`
- `src/supportops/__init__.py`
- `src/supportops/bootstrap.py`
- `src/supportops/cli.py`
- `src/supportops/contracts.py`
- `src/supportops/domain/knowledge.py`
- `src/supportops/errors.py`
- `src/supportops/knowledge_search.py`
- `src/supportops/knowledge_service.py`
- `src/supportops/knowledge/computer-no-network.md`
- `src/supportops/knowledge/identity-user-locked.md`
- `src/supportops/knowledge/onedrive-not-syncing.md`
- `src/supportops/knowledge/shared-mailbox-access-denied.md`
- `src/supportops/knowledge/sharepoint-access-denied.md`
- `tests/cli/test_cli.py`
- `tests/cli/test_knowledge_cli.py`
- `tests/contract/test_composition.py`
- `tests/integration/test_knowledge_corpus.py`
- `tests/__init__.py`
- `tests/security/test_knowledge_safety.py`
- `tests/smoke/test_startup.py`
- `tests/unit/__init__.py`
- `tests/unit/test_knowledge_search.py`

## Dev Agent Record

### Agent Model Used

GPT-5.6 Codex (`@dev`, Dex).

### Debug Log References

- Focused suite initially found one invalid Unicode fixture; corrected to a
  combining-mark-only query.
- Full regression initially found two stale `0.3.0` assertions; both were updated
  to the approved `0.4.0` version.
- `python -m build --no-isolation` lacked setuptools in the project venv;
  `uv build --offline` used the existing local build cache and succeeded.

### Completion Notes

- Implemented the complete CLI-first local knowledge search slice behind the
  replaceable `KnowledgeSearch` protocol.
- Added exactly five packaged, validated, non-executing runbooks.
- Corpus validation is fail-closed and returned source evidence is relative only.
- Search normalization, scores, matched terms, excerpts, and total ordering are
  deterministic and documented.

### Quality Gate Results

- Ruff: PASS, exit 0.
- MyPy strict: PASS, exit 0.
- Focused ST-04 after QA fixes: PASS, 43 tests; one conditional
  Windows symlink test skipped where symlink creation is unavailable.
- Full regression after QA fixes: PASS, 192 tests; one conditional Windows
  symlink test skipped where symlink creation is unavailable.
- Offline build: PASS, wheel and sdist 0.4.0 include all five runbooks.

### Evidence References

- `docs/support/knowledge-runbook-format.md`
- CLI demonstrations recorded during the implementation session.
- `docs/testing/evidence/ST-04.md`

## QA Results

### Gate: PASS

- Acceptance criteria: 20/20 verified after completion administration.
- Independent gates: Ruff PASS; strict MyPy PASS; full Pytest regression
  192 passed with one environment-conditioned Windows symlink skip; offline
  wheel/sdist build PASS; `git diff --check` PASS.
- Adversarial validation rejected missing, empty, heading-only, duplicated,
  reordered, case-changed, and extra body sections; empty corpus and arbitrary
  runtime-root override were also rejected or ignored as designed.
- Initial QA findings were corrected before PASS: incomplete body validation
  (High) and empty corpus health (Medium). Both are closed.
- Security: zero open Critical, High, or Medium findings; no shell/executor,
  network, UI, LLM, dynamic evaluation, automatic action, or Increment 5
  capability introduced.
- Residual limitation: lexical recall depends on curated aliases/keywords. The
  conditional symlink test is skipped where Windows lacks symlink privilege;
  containment remains covered by resolved-path tests and review.

Verdict recorded by `@qa` — Quinn on 2026-08-02. Status transition:
`Approved → Done` after implementation, remediation, evidence, and final gate.

## Change Log

| Date | Version | Description | Author |
|---|---:|---|---|
| 2026-08-02 | 0.1.0 | Initial ST-04 derived from approved Increment 4 scope and project architecture | @sm — River |
| 2026-08-02 | 0.1.1 | Explicit user authorization recorded; status set to Approved for `@dev` handoff | @sm — River |
| 2026-08-02 | 0.4.0 | Implemented local runbooks, deterministic lexical adapter, CLI, tests, and technical docs | @dev — Dex |
| 2026-08-02 | 0.4.1 | Independent QA PASS and completion evidence — Status: Approved → Done | @qa — Quinn / Orion |
