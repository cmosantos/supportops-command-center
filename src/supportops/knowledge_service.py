"""Application use case for read-only local knowledge search."""

from supportops.contracts import KnowledgeSearch
from supportops.domain.knowledge import SearchResult


class KnowledgeService:
    """Delegate a query to the replaceable knowledge port."""

    def __init__(self, search: KnowledgeSearch) -> None:
        self._search = search

    def search(self, query: str, limit: int = 10) -> tuple[SearchResult, ...]:
        return self._search.search(query, limit)
