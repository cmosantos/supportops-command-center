# Installation Guide

## Windows local

Install Python 3.12 and `uv`, clone/extract the project, then run from its root:

```powershell
uv sync --locked --extra dev
uv run supportops config validate
uv run supportops db status
uv run supportops db init
```

`db status` does not create a file. `db init` creates parent directories and
applies all checksummed migrations idempotently. Configure only non-secret values
through `SUPPORTOPS_DB_PATH`, `SUPPORTOPS_EXPORT_ROOT`, `SUPPORTOPS_LOG_LEVEL`,
`SUPPORTOPS_DB_BUSY_TIMEOUT_MS`, and optional `SUPPORTOPS_TRIAGE_POLICY_PATH`.
Paths may be absolute for an operator-controlled local installation; CLI callers
cannot select export filenames. Do not commit `.env`.

## Clean wheel installation

```powershell
uv run python -m build --no-isolation
py -3.12 -m venv .venv-clean-local
.\.venv-clean-local\Scripts\python.exe -m pip install dist\supportops_command_center-1.0.0-py3-none-any.whl
.\.venv-clean-local\Scripts\supportops.exe version
```

## Docker

```powershell
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Container paths are `/app/data/supportops.db` and `/app/exports`, backed by
separate named volumes. The UI binds host loopback on port 8501 by default.
`docker compose down` removes containers/network but retains volumes.

## Safe reset

There is deliberately no destructive reset command. Stop the application, back up
the database and exports, confirm exact application-owned targets, then follow an
organization-approved retention process. Never delete a broad directory or volume
as a troubleshooting shortcut.
