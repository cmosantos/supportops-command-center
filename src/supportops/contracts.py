"""Small structural contracts used by the composition root."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from supportops.config import Settings
from supportops.domain.knowledge import KnowledgeDocument, SearchResult


@runtime_checkable
class VersionProvider(Protocol):
    def get_version(self) -> str:
        """Return the canonical application version."""


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    name: str
    passed: bool
    detail: str


@runtime_checkable
class DiagnosticsProvider(Protocol):
    def run(self, settings: Settings) -> tuple[DiagnosticCheck, ...]:
        """Run in-process diagnostics only."""


@runtime_checkable
class KnowledgeSearch(Protocol):
    """Replaceable, implementation-independent knowledge search port."""

    def search(self, query: str, limit: int = 10) -> tuple[SearchResult, ...]:
        """Return deterministically ranked lexical matches."""

    def get(self, document_id: str) -> KnowledgeDocument:
        """Return one validated document by opaque identifier."""

    def health(self) -> bool:
        """Validate the entire configured corpus."""
