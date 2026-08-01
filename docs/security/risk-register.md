# Security and Technical Risk Register

| ID | Risk | Level | Architectural control | Residual/owner |
|---|---|---:|---|---|
| R-01 | Suggested command becomes execution | Critical | No executor port/adapter; negative scanning/tests | QA/Security; must be zero |
| R-02 | Approval replay for changed action | High | Bind ID, version, digest, snapshot; immutable decisions | QA validates replay cases |
| R-03 | Incorrect priority configuration | High | Schema/version/checksum; fail startup closed | Support Specialist approves matrix |
| R-04 | SQL injection or corrupt transaction | High | Bound parameters, constraints, unit of work | Data Engineer/QA |
| R-05 | Path traversal in knowledge/export | High | Fixed roots, generated filenames, containment checks | QA/Security |
| R-06 | Sensitive data in logs/exports | High | Minimization/redaction/safe errors | Retention policy pending |
| R-07 | Prompt injection/unsafe LLM output | High | Optional provider, structured validation, no tools | QA/Security |
| R-08 | Inconsistent deleted-record handling | Medium | One default repository policy; ADR-003 | Covered per consumer |
| R-09 | SQLite locks under Streamlit sessions | Medium | Short connections, transactions, busy timeout, tests | Local-scale limit documented |
| R-10 | Lexical search misses synonyms | Medium | Aliases/tags, explainable score | Accepted V1 limitation |
| R-11 | Sanitization damages technical evidence | Medium | Validate storage; escape rendering separately | Contract tests |
| R-12 | Ollama mock differs from real versions | Medium | Stable port and optional real smoke | Do not overclaim evidence |
| R-13 | Windows Docker volume differences | Medium | Build/start/restart persistence smoke | DevOps |
| R-14 | Accidental AIOX modification | Critical | Isolated root and scope verification | Orion/DevOps; must be zero |

## Security approval rule

Critical findings block the next increment. A waiver cannot authorize arbitrary
command execution, credential exposure, or modification of the AIOX core.

