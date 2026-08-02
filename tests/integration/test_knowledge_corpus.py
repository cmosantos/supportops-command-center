from pathlib import Path

import pytest

from supportops.knowledge_search import MarkdownKnowledgeSearch

ROOT = Path(__file__).parents[2] / "src" / "supportops" / "knowledge"


def test_packaged_corpus_has_exactly_five_valid_runbooks() -> None:
    adapter = MarkdownKnowledgeSearch(ROOT)
    assert adapter.health() is True
    assert len(list(ROOT.glob("*.md"))) == 5


@pytest.mark.parametrize(
    ("query", "document_id"),
    [
        ("shared mailbox", "shared-mailbox-access-denied"),
        ("conta bloqueada", "identity-user-locked"),
        ("sync pendente", "onedrive-not-syncing"),
        ("sem internet", "computer-no-network"),
        ("biblioteca bloqueada", "sharepoint-access-denied"),
    ],
)
def test_each_mandatory_runbook_is_retrievable(query: str, document_id: str) -> None:
    results = MarkdownKnowledgeSearch(ROOT).search(query)
    assert results[0].id == document_id
