# SupportOps Command Center

Local-first incident assistance for N1 and N2 support professionals.

## Current status

Phase 3, Increment 2 provides the Python 3.12 foundation plus SQLite incident
lifecycle through the canonical CLI. The implemented state machine is strictly
`OPEN ↔ CLOSED`. Triaging, runbooks, Streamlit, LLM/network providers, exports,
dashboard, restore, physical deletion, and command execution remain absent.

## Install

```powershell
uv venv --python 3.12 .venv
uv sync --extra dev
.\.venv\Scripts\supportops.exe config validate
.\.venv\Scripts\supportops.exe db status
.\.venv\Scripts\supportops.exe db init
```

Configuration is optional and uses the `SUPPORTOPS_` prefix. See `.env.example`.
LLM is disabled. `db status` does not create or migrate a missing database;
`db init` applies ordered, checksummed migrations transactionally and is
idempotent.

## CLI lifecycle

```powershell
.\.venv\Scripts\supportops.exe incident create --title "Network" --description "No access" --affected-party "Finance" --affected-service "LAN" --impact moderate --urgency high --symptoms "Timeout"
.\.venv\Scripts\supportops.exe incident get INCIDENT_ID
.\.venv\Scripts\supportops.exe incident list
.\.venv\Scripts\supportops.exe incident update INCIDENT_ID --expected-version 1 --title "Updated"
.\.venv\Scripts\supportops.exe incident close INCIDENT_ID
.\.venv\Scripts\supportops.exe incident reopen INCIDENT_ID
.\.venv\Scripts\supportops.exe incident history INCIDENT_ID
.\.venv\Scripts\supportops.exe incident delete INCIDENT_ID --reason "duplicate" --confirm
```

Deletion is logical, irreversible in V1, and excluded from operational queries.
There is no restore or physical-delete command. Approval identity is user-declared
and not authenticated; approval only records exact action metadata and never
executes the action.

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build
```

The application has no subprocess, shell, administrative executor, Streamlit,
network, or LLM adapter. SQL values are bound parameters and errors shown to the
operator omit SQL, database paths, sensitive payloads, and tracebacks.