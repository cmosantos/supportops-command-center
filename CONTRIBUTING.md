# Contributing

## Local setup

Use Python 3.12, `uv sync --locked --extra dev`, and synthetic data only. Work from
an approved story in `docs/stories/`; preserve CLI-first, shared application
services, deterministic offline behavior and the no-execution boundary.

## Required gate

```powershell
uv run ruff check .
uv run mypy src tests
uv run pytest -q
uv run python -m build --no-isolation
git diff --check
```

Add focused unit/integration/CLI/security tests without weakening regression.
Update story checklists, evidence, traceability and exact File List. Keep commits
limited to one increment and use imperative messages such as `chore: harden V1 delivery`.

## Security and data rules

Never commit `.env`, credentials, tokens, private keys, personal/production
incidents, SQLite/journal files, exports, logs, caches, virtual environments or
screenshots containing user data. No shell/subprocess or administrative executor,
dynamic evaluation, unsafe deserialization, LLM/vector/network product dependency,
or direct Streamlit access to SQLite/filesystems is accepted.

Human approval is required for a license decision, remote creation/configuration,
push, pull request, tag, release, registry/image publication, external action,
scope expansion and destructive persistent-data operation.
