# Incremental Quality Gates

## G0 — Architecture entry

Approved story, ADRs, contracts, SQLite design, traceability, risks, and explicit
Phase 2 approval. No implementation begins before this gate.

## G1 — Domain and CLI foundation

Models/configuration/policies pass unit and contract tests. Essential capabilities
are exposed through application services and CLI before UI work.

## G2 — Persistence and audit

Real temporary SQLite proves bootstrap, transactions, foreign keys, history,
soft deletion, approvals, filters, and rollback. Physical delete is absent.

## G3 — Knowledge and deterministic analysis

Five runbooks are found; evidence questions precede solutions; plans maintain safe
order; commands remain suggestions.

## G4 — Documentation, exports, Streamlit, and dashboard

Streamlit reuses application services. Dashboard is observational. Exports are
safe and consistent. Full earlier regression remains green.

## G5 — Optional provider

Fake/mock tests cover valid, timeout, unavailable, invalid, and fallback cases.
The required suite passes with Ollama disabled and without network.

## G6 — Security

Any arbitrary shell path, effective SQL/path injection, exposed secret, approval
bypass, automatic sensitive action, or open critical finding yields FAIL.

## G7 — Release candidate

Unit, integration, startup, CLI E2E, Streamlit smoke/E2E, Docker build/start/restart,
security review, and clean README reproduction pass. AIOX-required quality commands
are run when available and applicable; Python checks and pytest are mandatory.

Failure blocks the next increment. Fix and regression precede advancement. A human
gate remains required between each main phase.

