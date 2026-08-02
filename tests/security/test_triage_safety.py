import ast
from pathlib import Path

SOURCE = Path(__file__).parents[2] / "src" / "supportops"


def test_triage_repository_and_service_have_no_mutation_or_execution_surface() -> None:
    repository_tree = ast.parse(
        (SOURCE / "repositories.py").read_text(encoding="utf-8")
    )
    triage_methods = {
        node.name
        for node in ast.walk(repository_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "update_snapshot" not in triage_methods
    assert "delete_snapshot" not in triage_methods
    for path in (
        SOURCE / "triage_engine.py",
        SOURCE / "triage_service.py",
        SOURCE / "triage_policy.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        assert imports.isdisjoint({"subprocess", "os", "socket", "requests", "httpx"})


def test_cli_still_contains_no_sql() -> None:
    tree = ast.parse((SOURCE / "cli.py").read_text(encoding="utf-8"))
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert calls.isdisjoint({"execute", "executemany", "executescript"})
