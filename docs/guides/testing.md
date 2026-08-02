# Testing and Reproduction

```powershell
uv sync --locked --extra dev
uv run ruff check .
uv run mypy src tests
uv run pytest -q
uv run python -m build --no-isolation
git diff --check
```

Focused hardening tests cover clean migration/integrity/foreign keys, artifact
inventory, Docker/Compose static controls, workflow least permissions, prohibited
capabilities, secret/PII/runtime-artifact patterns and documentation readiness.
Real Streamlit smoke is bounded and uses loopback plus temporary DB/export roots.

Docker reproduction:

```powershell
docker compose -p supportops-st08-test config
docker compose -p supportops-st08-test build
docker compose -p supportops-st08-test up -d
docker compose -p supportops-st08-test ps
docker compose -p supportops-st08-test restart app
docker compose -p supportops-st08-test down
```

Do not use `down -v` before database/export persistence assertions. CI is prepared
locally; only a future GitHub run can establish remote workflow evidence.
