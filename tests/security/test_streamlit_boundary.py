"""Streamlit remains a thin, safe presentation adapter."""

import ast
from pathlib import Path


def test_streamlit_has_no_infrastructure_or_unsafe_imports() -> None:
    path = Path("src/supportops/streamlit_app.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {"sqlite3", "pathlib", "subprocess", "os", "requests"}
    forbidden_supportops = {
        "supportops.repositories",
        "supportops.persistence",
        "supportops.exporters",
        "supportops.knowledge_search",
        "supportops.triage_engine",
        "supportops.triage_policy",
    }
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names if alias.name in forbidden)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module in forbidden_supportops or node.module in forbidden:
                found.append(node.module)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"open", "eval", "exec"}
        ):
            found.append(node.func.id)
    assert found == []
    assert "unsafe_allow_html" not in path.read_text(encoding="utf-8")
