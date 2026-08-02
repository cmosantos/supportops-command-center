"""Static delivery checks that run without Docker or network access."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_secure_container_and_persistent_volume_contract() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "USER 10001:10001" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "ENTRYPOINT" in dockerfile and "streamlit" in dockerfile
    assert dockerfile.count("FROM ") == 2
    assert "COPY pyproject.toml uv.lock README.md ./" in dockerfile
    assert "uv sync --locked --no-dev --no-install-project" in dockerfile
    assert "UV_PROJECT_ENVIRONMENT=/opt/venv" in dockerfile
    assert "COPY --from=builder /opt/venv /opt/venv" in dockerfile
    assert "uv==0.11.19" in dockerfile
    assert "uv pip install" in dockerfile and "--no-deps" in dockerfile
    assert "pip install --no-cache-dir /tmp/*.whl" not in dockerfile
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "127.0.0.1:${SUPPORTOPS_PORT:-8501}:8501" in compose
    assert "supportops_db:/app/data" in compose
    assert "supportops_exports:/app/exports" in compose
    assert "ollama" not in compose.casefold()


def test_dockerignore_rejects_runtime_and_secret_artifacts() -> None:
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    required = {
        ".git",
        ".env*",
        ".venv*",
        "tests",
        "data",
        "exports",
        "*.db",
        "*.sqlite*",
        "screenshots",
        "logs",
    }
    assert required <= set(ignored)
    assert "src" not in ignored


def test_github_workflow_is_validation_only_and_least_privilege() -> None:
    workflow = (ROOT / ".github/workflows/quality.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in workflow
    commands = (
        "ruff check .",
        "mypy src tests",
        "pytest -q",
        "build --no-isolation",
    )
    for command in commands:
        assert command in workflow
    lowered = workflow.casefold()
    for forbidden in ("deploy", "publish", "docker login", "secrets."):
        assert forbidden not in lowered


def test_publication_material_keeps_human_decisions_pending() -> None:
    assert not (ROOT / "LICENSE").exists()
    readiness = (ROOT / "docs/publication/github-readiness.md").read_text(
        encoding="utf-8"
    )
    assert "[ ] Select a definitive license" in readiness
    assert "[ ] Configure remote" in readiness
    assert "No item above was executed" in readiness
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "security@" not in security


def test_required_professional_docs_exist_and_are_nonempty() -> None:
    required = (
        "README.md",
        "CHANGELOG.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "docs/guides/installation.md",
        "docs/guides/usage.md",
        "docs/guides/demo.md",
        "docs/guides/testing.md",
        "docs/guides/security.md",
        "docs/guides/screenshots.md",
        "docs/known-limitations.md",
        "docs/roadmap.md",
        "docs/release-notes/v1.0.0.md",
        "docs/publication/github-readiness.md",
    )
    for relative in required:
        assert (ROOT / relative).stat().st_size > 100
