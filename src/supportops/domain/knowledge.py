"""Immutable knowledge models exposed by the application boundary."""

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocument(BaseModel):
    """One validated runbook rooted in the configured knowledge directory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=160)
    aliases: tuple[str, ...] = Field(min_length=1)
    category: str = Field(min_length=1, max_length=80)
    symptoms: tuple[str, ...] = Field(min_length=1)
    keywords: tuple[str, ...] = Field(min_length=1)
    risk_notes: tuple[str, ...] = Field(min_length=1)
    escalation_criteria: tuple[str, ...] = Field(min_length=1)
    revision: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    source_path: str = Field(pattern=r"^[^\\/:]+\.md$")
    content: str = Field(min_length=1)


class SearchResult(BaseModel):
    """Explainable lexical result containing display metadata and evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    category: str
    aliases: tuple[str, ...]
    symptoms: tuple[str, ...]
    keywords: tuple[str, ...]
    risk_notes: tuple[str, ...]
    escalation_criteria: tuple[str, ...]
    revision: str
    source_path: str
    score: int = Field(gt=0)
    matched_terms: tuple[str, ...] = Field(min_length=1)
    excerpt: str = Field(min_length=1, max_length=240)
