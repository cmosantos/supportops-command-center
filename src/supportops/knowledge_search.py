"""Safe local Markdown adapter and deterministic lexical ranking."""

from __future__ import annotations

import re
import tomllib
import unicodedata
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from supportops.domain.knowledge import KnowledgeDocument, SearchResult
from supportops.errors import InputValidationError, KnowledgeError, NotFoundError

_WORD = re.compile(r"[a-z0-9]+")
_SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_WEIGHTS = {
    "title": 50,
    "aliases": 40,
    "symptoms": 30,
    "keywords": 25,
    "content": 10,
}
_MAX_LIMIT = 100
_REQUIRED_HEADINGS = (
    "# Objetivo",
    "## Evidências seguras",
    "## Orientação não executável",
    "## Pare e escale",
)


def normalize_text(value: str) -> str:
    """Normalize Unicode, accents, case, and punctuation for matching."""

    decomposed = unicodedata.normalize("NFKD", value.casefold())
    unaccented = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(_WORD.findall(unaccented))


def query_terms(query: str) -> tuple[str, ...]:
    """Return sorted unique terms or reject queries without lexical content."""

    terms = tuple(sorted(set(normalize_text(query).split())))
    if not terms:
        raise InputValidationError("Knowledge query must contain searchable text.")
    return terms


class MarkdownKnowledgeSearch:
    """Fail-closed adapter over UTF-8 Markdown files in one fixed root."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def health(self) -> bool:
        self._load_corpus()
        return True

    def get(self, document_id: str) -> KnowledgeDocument:
        if not _SAFE_ID.fullmatch(document_id):
            raise InputValidationError("Knowledge document identifier is invalid.")
        for document in self._load_corpus():
            if document.id == document_id:
                return document
        raise NotFoundError("Knowledge document was not found.")

    def search(self, query: str, limit: int = 10) -> tuple[SearchResult, ...]:
        terms = query_terms(query)
        if not 1 <= limit <= _MAX_LIMIT:
            raise InputValidationError(
                "Knowledge result limit must be between 1 and 100."
            )
        results = [
            result
            for document in self._load_corpus()
            if (result := self._score(document, terms)) is not None
        ]
        results.sort(
            key=lambda item: (
                -item.score,
                normalize_text(item.title),
                item.id,
                item.source_path,
            )
        )
        return tuple(results[:limit])

    def _load_corpus(self) -> tuple[KnowledgeDocument, ...]:
        try:
            root = self._root.resolve(strict=True)
        except (OSError, RuntimeError):
            raise KnowledgeError(
                "Knowledge corpus is unavailable or invalid."
            ) from None
        if not root.is_dir() or self._root.is_symlink():
            raise KnowledgeError("Knowledge corpus is unavailable or invalid.")
        documents: list[KnowledgeDocument] = []
        identifiers: set[str] = set()
        try:
            candidates = sorted(root.glob("*.md"), key=lambda path: path.name)
        except OSError:
            raise KnowledgeError(
                "Knowledge corpus cannot be inspected safely."
            ) from None
        for candidate in candidates:
            document = self._load_document(root, candidate)
            if document.id in identifiers:
                raise KnowledgeError(
                    "Knowledge corpus contains duplicate document identifiers."
                )
            identifiers.add(document.id)
            documents.append(document)
        if not documents:
            raise KnowledgeError("Knowledge corpus contains no valid runbooks.")
        return tuple(documents)

    @staticmethod
    def _load_document(root: Path, candidate: Path) -> KnowledgeDocument:
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            if candidate.is_symlink() or not resolved.is_file():
                raise KnowledgeError("Knowledge corpus contains an unsafe file.")
            raw = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise KnowledgeError(
                "Knowledge corpus contains unsupported text encoding."
            ) from None
        except KnowledgeError:
            raise
        except (OSError, RuntimeError, ValueError):
            raise KnowledgeError(
                "Knowledge corpus contains an unsafe or unreadable file."
            ) from None
        try:
            metadata, content = _parse_markdown(raw)
            return KnowledgeDocument.model_validate(
                {**metadata, "source_path": candidate.name, "content": content}
            )
        except (ValidationError, ValueError, tomllib.TOMLDecodeError, TypeError):
            raise KnowledgeError(
                "Knowledge corpus contains an invalid runbook."
            ) from None

    @staticmethod
    def _score(
        document: KnowledgeDocument, terms: tuple[str, ...]
    ) -> SearchResult | None:
        fields = {
            "title": set(normalize_text(document.title).split()),
            "aliases": set(normalize_text(" ".join(document.aliases)).split()),
            "symptoms": set(normalize_text(" ".join(document.symptoms)).split()),
            "keywords": set(normalize_text(" ".join(document.keywords)).split()),
            "content": set(normalize_text(document.content).split()),
        }
        matched: list[str] = []
        score = 0
        for term in terms:
            term_matched = False
            for field, words in fields.items():
                if term in words:
                    score += _WEIGHTS[field]
                    term_matched = True
            if term_matched:
                matched.append(term)
        if not matched:
            return None
        return SearchResult(
            **document.model_dump(exclude={"content"}),
            score=score,
            matched_terms=tuple(matched),
            excerpt=_excerpt(document.content, tuple(matched)),
        )


def _parse_markdown(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("+++\n"):
        raise ValueError("missing front matter")
    closing = raw.find("\n+++\n", 4)
    if closing < 0:
        raise ValueError("unterminated front matter")
    metadata = tomllib.loads(raw[4:closing])
    content = raw[closing + 5 :].strip()
    if not content:
        raise ValueError("empty content")
    _validate_canonical_sections(content)
    return metadata, content


def _validate_canonical_sections(content: str) -> None:
    """Require one ordered, non-empty canonical section for every runbook."""

    lines = content.splitlines()
    headings = [line.strip() for line in lines if line.lstrip().startswith("#")]
    if headings != list(_REQUIRED_HEADINGS):
        raise ValueError("invalid canonical headings")
    positions = [
        next(index for index, line in enumerate(lines) if line.strip() == heading)
        for heading in _REQUIRED_HEADINGS
    ]
    boundaries = [*positions[1:], len(lines)]
    for start, end in zip(positions, boundaries, strict=True):
        if not any(line.strip() for line in lines[start + 1 : end]):
            raise ValueError("empty canonical section")


def _excerpt(content: str, terms: tuple[str, ...]) -> str:
    paragraphs = [
        " ".join(part.split())
        for part in re.split(r"\n\s*\n", content)
        if part.strip() and not part.lstrip().startswith("#")
    ]
    ranked = sorted(
        enumerate(paragraphs),
        key=lambda item: (
            -sum(term in set(normalize_text(item[1]).split()) for term in terms),
            item[0],
        ),
    )
    excerpt = ranked[0][1]
    return excerpt if len(excerpt) <= 240 else excerpt[:237].rstrip() + "..."
