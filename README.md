# SupportOps Command Center

Local-first, deterministic incident assistance for N1/N2 service-desk teams. The
V1 provides audited incident lifecycle, evidence-based triage, offline runbooks,
nine-section ticket documentation, safe exports, and a Streamlit dashboard over
one shared application layer.

> Publication status: prepared locally, not published. A definitive license,
> security contact, Git remote, release tag, and push require human decisions.

## Why it is useful

- One traceable path from registration through triage, performed work and export.
- Deterministic decisions and lexical ranking that remain explainable offline.
- CLI-first behavior reused by a thin Streamlit interface.
- SQLite history, soft deletion, immutable triage/document revisions and safe
  Markdown/JSON export.
- No command execution, administrative action, LLM, embeddings, vector database,
  ticket-system integration, or required outbound service.

## Requirements and installation

Use Python 3.12 and [uv](https://docs.astral.sh/uv/) locally:

```powershell
uv sync --locked --extra dev
uv run supportops config validate
uv run supportops db status
uv run supportops db init
```

Configuration uses `SUPPORTOPS_` environment variables. Copy `.env.example` only
for non-sensitive local configuration. Defaults store the database at
`data/supportops.db` and exports under `exports/`; both paths are configurable.
See [installation](docs/guides/installation.md) for Windows and containers.

## Run

```powershell
# CLI
uv run supportops doctor
uv run supportops incident list
uv run supportops knowledge search "sincronização OneDrive"

# Web UI (then open http://127.0.0.1:8501)
uv run streamlit run src/supportops/streamlit_app.py --server.address=127.0.0.1
```

The UI can initialize/check the database; register, query, update, close, reopen
and logically delete incidents; display history; run triage; search runbooks;
record performed procedures; generate/export documentation; and show dashboard
metrics. It accesses these operations only through the application facade.

## Docker Compose

```powershell
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Open `http://127.0.0.1:8501`. The image runs as UID/GID `10001`, drops Linux
capabilities, uses a read-only root filesystem, and persists SQLite and exports in
separate named volumes. Change only the host port with `SUPPORTOPS_PORT`. Stop
without deleting user data using `docker compose down` (do not add `--volumes`).

## Synthetic end-to-end demonstration

```powershell
uv run supportops db init
$incident = (uv run supportops incident create --title "Synthetic OneDrive sync" --description "Training record; client paused" --affected-party "Example User" --affected-service "OneDrive" --impact moderate --urgency moderate --symptoms "No synchronization" --category storage --actor demo-analyst | ConvertFrom-Json).id
uv run supportops incident list
uv run supportops triage run $incident --evidence-json '{"impact":"moderate","urgency":"moderate"}' --actor demo-analyst --format json
uv run supportops knowledge search "onedrive sincronização" --format json
uv run supportops performed record $incident --description "Checked client state" --result "Client was paused" --actor demo-analyst
uv run supportops document generate $incident --actor demo-analyst --format json
uv run supportops document show $incident --revision 1 --format json
uv run supportops export $incident --revision 1 --format markdown
uv run supportops export $incident --revision 1 --format json --output json
```

See the [complete demo](docs/guides/demo.md) and [usage guide](docs/guides/usage.md).

## Architecture

```text
CLI ---------+                         +--> SQLite (database volume)
             +--> Application facade -+--> Markdown runbooks (read-only package)
Streamlit ---+                         +--> exporters (exports volume)
```

Domain and application services own validation and policy. Presentation adapters
do not contain SQL, filesystem export logic, ranking rules or arbitrary execution.
See the [architecture](docs/architecture/overview.md).

## Quality and security

```powershell
uv run ruff check .
uv run mypy src tests
uv run pytest -q
uv run python -m build --no-isolation
git diff --check
```

Input is validated, SQL uses parameters, migrations are checksummed and exports
are contained, atomic and non-overwriting. Incident text is operator-controlled:
do not enter credentials or unnecessary personal data. Review
[SECURITY.md](SECURITY.md), the [test guide](docs/guides/testing.md), and the
[security boundary](docs/guides/security.md).

## Troubleshooting

- `db status` is intentionally non-mutating; run `db init` to apply migrations.
- Invalid configuration returns a safe error and exit code `2`; unexpected errors
  return `1`; successful commands and an empty knowledge search return `0`.
- If port 8501 is busy, use `SUPPORTOPS_PORT=8502` for Compose or choose another
  Streamlit `--server.port`.
- Docker volume write failures usually mean ownership was changed outside the
  container; inspect the exact named volume instead of deleting it.

## Limitations and roadmap

V1 is single-node SQLite with normal file-locking/scale limits. Actor identifiers
are declared, not authenticated. Soft deletion is irreversible and has no restore.
Search is lexical and depends on curated aliases. There is no ticket integration,
SLA pause calculation, automatic retention, shell/admin execution, or guarantee
that incident text is free of sensitive data. See [known limitations](docs/known-limitations.md).

Increment 7 (optional Ollama experimentation) remains outside V1 and has no
timeline. Any future provider must preserve deterministic offline operation and
the no-execution boundary. See the [roadmap](docs/roadmap.md).

## Contributing and publication

Read [CONTRIBUTING.md](CONTRIBUTING.md). Before publishing, a human must select a
license and security contact, configure repository controls, review screenshots,
create a remote, push and deliberately tag/release. No `LICENSE` is included.
