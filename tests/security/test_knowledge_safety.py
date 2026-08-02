from pathlib import Path

import pytest

from supportops.errors import KnowledgeError
from supportops.knowledge_search import MarkdownKnowledgeSearch
from tests.unit.test_knowledge_search import write_runbook


def test_symlink_escape_is_never_read(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside.md"
    write_runbook(tmp_path, filename="outside.md")
    root.mkdir()
    link = root / "escape.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(KnowledgeError, match="unsafe"):
        MarkdownKnowledgeSearch(root).health()


def test_nested_outside_content_is_not_indexed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    write_runbook(root)
    write_runbook(root / "nested", document_id="outside", filename="outside.md")
    assert all(
        result.id != "outside"
        for result in MarkdownKnowledgeSearch(root).search("rede")
    )


def test_production_knowledge_modules_have_no_dangerous_capabilities() -> None:
    source_root = Path(__file__).parents[2] / "src" / "supportops"
    source = "\n".join(
        (source_root / name).read_text(encoding="utf-8")
        for name in ("knowledge_search.py", "knowledge_service.py")
    )
    for prohibited in (
        "subprocess",
        "os.system",
        "eval(",
        "exec(",
        "requests",
        "httpx",
        "openai",
        "ollama",
    ):
        assert prohibited not in source.lower()
