# SupportOps Command Center

Local-first incident assistance for N1 and N2 support professionals.

## Current status

Phase 2 — architecture only. No application functionality has been implemented.

The approved product scope, architecture, domain model, SQLite design, contracts,
ADRs, traceability matrix, implementation plan, progress, and pending decisions
are under `docs/`.

## Governance boundaries

- Everything for this product remains inside this directory.
- CLI capabilities must precede Streamlit capabilities.
- The application will suggest commands but will never execute them.
- Ollama will be optional and disabled by default.
- Implementation may begin only after explicit Phase 2 approval.

