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
| RQ-06 Five local Markdown runbooks | ST-06 Knowledge | T-I-020 all five found; T-U-050 normalized search; T-I-021 corrupt file; T-S-020 traversal |
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

