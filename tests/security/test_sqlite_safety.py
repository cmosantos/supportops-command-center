import ast
from pathlib import Path

SOURCE = Path(__file__).parents[2] / "src" / "supportops"


def test_no_physical_delete_or_restore_contract_exists() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in SOURCE.rglob("*.py")
    )
    forbidden_sql = "DELETE" + " FROM"
    assert forbidden_sql not in source.upper()
    assert "def hard_delete" not in source
    assert "def restore" not in source


def test_cli_contains_no_sql_and_events_have_no_mutators() -> None:
    cli_tree = ast.parse((SOURCE / "cli.py").read_text(encoding="utf-8"))
    calls = {
        node.func.attr
        for node in ast.walk(cli_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert calls.isdisjoint({"execute", "executemany", "executescript"})
    repository_tree = ast.parse(
        (SOURCE / "repositories.py").read_text(encoding="utf-8")
    )
    methods = {
        node.name
        for node in ast.walk(repository_tree)
        if isinstance(node, ast.FunctionDef)
    }
    assert "update_event" not in methods
    assert "delete_event" not in methods
