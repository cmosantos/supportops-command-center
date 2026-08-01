# SupportOps Command Center

Local-first incident assistance for N1 and N2 support professionals.

## Current status

Phase 3, Increment 1 implements the Python 3.12 foundation and canonical CLI:
validated settings, a validation-only 4x4 matrix contract, safe errors/redaction,
a composition root, and offline diagnostics. Incidents, triage, SQLite, Streamlit,
runbooks, Ollama, network clients, and command execution are not implemented.

## Install and run

```powershell
uv venv --python 3.12 .venv
uv sync --extra dev
.\.venv\Scripts\supportops.exe version
.\.venv\Scripts\supportops.exe config validate
.\.venv\Scripts\supportops.exe doctor
```

Python must satisfy `>=3.12,<3.13`. Configuration is optional; copy
`.env.example` to `.env` only for overrides. Variables use the `SUPPORTOPS_`
prefix. LLM is disabled and cannot be enabled in this increment. Invalid values
produce an actionable error without the rejected value or a stack trace.

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build
```

## Security boundaries

The application has no shell, subprocess, administrative command, database,
network, UI, or LLM adapter. `doctor` performs in-process checks only. `.env` is
ignored, and examples contain no credentials.