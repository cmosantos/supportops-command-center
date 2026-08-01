import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[2] / "src" / "supportops"
PROHIBITED_CALLS = {"eval", "exec", "__import__"}
PROHIBITED_OS_CALLS = {"system", "popen"}
FORBIDDEN_IMPORT_ROOTS = {
    "streamlit",
    "ollama",
    "requests",
    "httpx",
    "subprocess",
}


def test_application_source_has_no_execution_or_forbidden_adapter_apis() -> None:
    violations: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                        violations.append(f"{path}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                    violations.append(f"{path}:{node.lineno}: from {node.module}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in PROHIBITED_CALLS:
                    violations.append(f"{path}:{node.lineno}: {node.func.id}")
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"
                    and node.func.attr in PROHIBITED_OS_CALLS
                ):
                    violations.append(f"{path}:{node.lineno}: os.{node.func.attr}")

    assert violations == []


def test_composition_root_has_no_forbidden_import_text() -> None:
    source = (SOURCE_ROOT / "bootstrap.py").read_text(encoding="utf-8").lower()
    for forbidden in FORBIDDEN_IMPORT_ROOTS:
        assert forbidden not in source
