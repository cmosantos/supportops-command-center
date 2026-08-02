# ruff: noqa: S603, S607
"""Repository-scope and dependency metadata hardening checks."""

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".svg",
    ".txt",
    ".ps1",
    ".example",
}
FORBIDDEN_NAMES = {".env", "secrets.toml", "id_rsa", "id_ed25519"}


def _project_files() -> tuple[Path, ...]:
    ignored_parts = {
        ".git",
        ".venv",
        ".venv-smoke",
        "build",
        "dist",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "data",
        "exports",
        "screenshots",
        "logs",
    }
    files = []
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if not path.is_file() or ignored_parts.intersection(parts):
            continue
        if any(part.startswith(".venv-") for part in parts):
            continue
        files.append(path)
    return tuple(files)


def test_no_forbidden_runtime_artifacts_in_project_inventory() -> None:
    violations = []
    for path in _project_files():
        relative = path.relative_to(ROOT)
        lowered = path.name.casefold()
        if lowered in FORBIDDEN_NAMES:
            violations.append(str(relative))
        if path.suffix.casefold() in {".db", ".sqlite", ".sqlite3", ".log"}:
            violations.append(str(relative))
        if lowered.endswith((".db-wal", ".db-shm")):
            violations.append(str(relative))
    assert violations == []


def test_no_committed_secret_shapes_or_absolute_developer_paths() -> None:
    secret = re.compile(
        r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"
    )
    private_key = "-----BEGIN " + "PRIVATE KEY-----"
    violations = []
    for path in _project_files():
        if path.suffix.casefold() not in TEXT_SUFFIXES and path.name != "Dockerfile":
            continue
        text = path.read_text(encoding="utf-8")
        if secret.search(text) or private_key in text:
            violations.append(str(path.relative_to(ROOT)))
        normalized = text.casefold().replace("/", "\\")
        windows_user_path = re.search(r"[a-z]:\\users\\[^\\]+\\", normalized)
        unix_user_path = re.search(
            r"(?<![a-z0-9_])/(?:home|users)/[^/\s]+/", text.casefold()
        )
        if windows_user_path or unix_user_path:
            violations.append(str(path.relative_to(ROOT)))
    assert violations == []


def test_locked_product_dependencies_exclude_llm_vector_and_network_clients() -> None:
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8").casefold()
    dependencies = metadata.split("[project.optional-dependencies]", maxsplit=1)[0]
    for forbidden in (
        '"openai',
        '"ollama',
        '"langchain',
        '"chromadb',
        '"faiss',
        '"requests',
        '"httpx',
    ):
        assert forbidden not in dependencies


def test_screenshot_helper_uses_only_synthetic_values_and_contained_root() -> None:
    script = (ROOT / "scripts/prepare_screenshot_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "GetRelativePath($project, $root)" in script
    assert "IsPathRooted($relative)" in script
    assert "ReparsePoint" in script
    assert "Test-Path -LiteralPath" in script
    assert "Example User" in script
    assert "demo-analyst" in script
    assert "Remove-Item" not in script


def test_screenshot_helper_rejects_preexisting_reparse_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = ROOT / ".screenshot-reparse-test"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    try:
        result = subprocess.run(
            [
                "pwsh",
                "-NoProfile",
                "-File",
                str(ROOT / "scripts/prepare_screenshot_demo.ps1"),
                "-RuntimeRoot",
                link.name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode != 0
        assert "reparse point" in (result.stdout + result.stderr).casefold()
        assert tuple(outside.iterdir()) == ()
    finally:
        link.unlink(missing_ok=True)
