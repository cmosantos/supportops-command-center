# Requirements → Stories → Tests

Status: Planned. Test IDs define future evidence; they are not implemented or
reported as passing in Phase 2.

| Requirement | Canonical story | Planned evidence |
|---|---|---|
| RQ-01 Incident registration and validation | ST-01 Registration | T-U-001 valid model; T-U-002 required fields; T-S-001 hostile input; T-I-001 CLI persistence |
| RQ-02 Classification and configurable priority | ST-02 Triage | T-U-010 matrix combinations; T-U-011 invalid config; T-C-001 schema/version; T-E-010 config change |
| RQ-03 Missing evidence and questions first | ST-03 Evidence | T-U-020 gaps; T-U-021 answered evidence; T-E-020 questions precede solution |
| RQ-04 Hypothesis tree | ST-04 Hypotheses | T-C-010 required fields; T-U-030 confidence/source; T-E-030 evaluation in documentation |
| RQ-05 Safe troubleshooting order | ST-05 Troubleshooting | T-U-040 stage order; T-U-041 escalation; T-S-010 sensitive action; T-E-040 full plan |
| RQ-06 Five local Markdown runbooks | ST-04 Knowledge | T4-INT all five found; T4-UNIT normalized/ranked search; T4-INVALID corrupt corpus; T4-SEC traversal |
| RQ-07 Structured command suggestions | ST-07 Safe actions | T-C-020 metadata; T-U-060 approval marker; T-S-030 no executor/shell |
| RQ-08 Persisted human approval | ST-07 Safe actions | T-I-030 exact action record; T-I-031 no replay; T-S-031 rejection remains non-executable |
| RQ-09 Ticket documentation | ST-08 Documentation | T-C-030 nine sections; T-I-040 persisted facts; T-S-040 redacted output |
| RQ-10 History, close/reopen, soft delete | ST-09 Lifecycle | T-I-050 filters; T-I-051 reopen; T-I-052 events; T-I-053 soft delete; T-I-054 no confirmation |
| RQ-11 Dashboard metrics | ST-10 Metrics | T-U-070 six metrics; T-I-060 real SQLite; T-U-071 deleted excluded; T-C-050 observational only |
| RQ-12 Markdown and JSON export | ST-11 Export | T-C-060 formats; T-I-070 persisted snapshot; T-S-060 safe path |
| RQ-13 CLI First and Streamlit | ST-12 Interfaces | T-E-080 CLI journey; T-C-070 shared services; T-E-081 UI journey; T-S-070 safe rendering |
| RQ-14 SQLite automatic bootstrap | ST-13 Infrastructure | T-I-080 creation/migrations; T-I-081 rollback/locking; T-D-001 startup; T-D-002 persistence |
| RQ-15 Optional Ollama and future providers | ST-14 LLM adapter | T-C-080 isolation; T-U-090 valid fake; T-U-091 timeout/invalid/fallback; T-E-090 disabled mode |
| RQ-16 Security and safe errors | ST-15 Hardening | T-S-090 secret scan; T-S-091 no credential fields; T-S-092 redaction; T-S-093 injection; T-S-094 no automatic action |
| RQ-17 Quality, Docker, reproducible docs | ST-16 Delivery | T-I-100 clean install; T-E-100 real E2E; T-Q-001 gates; T-Q-002 AC/file-list evidence |

## Traceability policy

1. A future story may refine tests but cannot remove a mapped requirement without
   Product Owner approval.
2. A component is not complete until its mapped tests run and evidence is recorded.
3. Integration and E2E completion cannot be claimed from mocks alone.
4. Real-Ollama smoke is optional and must be labeled optional.
5. Test outcomes include command, date, environment, exit code, and counts.


## ST-03 implemented traceability

| Requirement / AC group | Story | Implemented evidence |
|---|---|---|
| Versioned fail-closed policy and exact 4x4 matrix | ST-03 AC 1-9 | `T3-CFG-*`, `T3-MX-01..16`, `T3-PRI-*`, `T3-IMP-*`, `T3-URG-*` |
| Routing, escalation and N1/N2 recommendation | ST-03 AC 10-14 | `T3-ESC-*`, `T3-LVL-*` |
| DQ-01..12, gaps and structured risk | ST-03 AC 15-18 | `T3-DQ-01..12`, `T3-RISK-*`, `T3-GAP-*` |
| STOP-01..07 and no side effects | ST-03 AC 19-20 | `T3-STOP-01..09`, real SQLite no-lifecycle/no-approval assertion |
| CLI human/JSON and hidden incidents | ST-03 AC 21-23 | `T3-CLI-01..04` |
| Atomic immutable persistence and re-triage | ST-03 AC 24-26 | `T3-INT-01..02`, v1→v2 migration, FK orphan and fault rollback |
| Hostile input, redaction and prohibited capabilities | ST-03 AC 27-29 | `T3-SEC-01..03`, AST and CLI canary tests |
| Full gates and isolation | ST-03 AC 30-31 | Ruff, MyPy, Pytest, build/wheel, CLI smoke and Git evidence in `docs/testing/evidence/ST-03.md` |

## ST-04 implemented traceability

| Requirement / AC group | Story | Implemented evidence |
|---|---|---|
| Runbook format and five mandatory documents | ST-04 AC 1-3 | Format specification, packaged corpus validation, five-scenario integration tests |
| Replaceable port and deterministic lexical search | ST-04 AC 4-9 | Protocol/composition tests; normalization, field weights, ranking, tie and repeatability unit tests |
| Human/JSON CLI and no-result behavior | ST-04 AC 10-12 | Knowledge CLI tests and recorded demonstrations |
| Invalid corpus and filesystem containment | ST-04 AC 13-16 | Missing/empty/corrupt/duplicate/encoding/structure tests; traversal, outside-root and conditional symlink tests |
| Offline scope, gates, QA and completion | ST-04 AC 17-20 | Prohibited-capability scan, Ruff, MyPy, 192-test regression, offline build, independent QA and `docs/testing/evidence/ST-04.md` |

## ST-05 implemented traceability

| Requirement / AC group | Story | Implemented evidence |
|---|---|---|
| Performed/suggested separation and traceability | ST-05 AC 1-5, 9 | Typed domain tests, real-SQLite ordered history and invalid-reference rollback |
| Persisted nine-section revisions | ST-05 AC 6-11 | Generation/history integration and CLI journey tests |
| Markdown/JSON adapters | ST-05 AC 12-15 | Determinism, strict JSON, Unicode, heading-order and hostile-content unit tests |
| Fixed-root safe publication | ST-05 AC 16-18 | Traversal, absolute/drive/alternate path, invalid-root and collision security tests |
| CLI and safe errors | ST-05 AC 19-22 | Performed/document/export CLI E2E plus complete ST-01–04 regression |
# ST-06 traceability

- Web/application boundary and safe imports: AC 2-4, 22-23 —
  `tests/security/test_streamlit_boundary.py`.
- Real SQLite dashboard, deleted exclusion, lifecycle duration, filtering, and
  export content: AC 18-20 — `tests/integration/test_web_facade.py`.
- Real Streamlit clean startup: AC 24-26 —
  `tests/presentation/test_streamlit_app.py`.
