# ADR-005: Lexical Markdown knowledge search

Status: Accepted for Phase 2

## Decision

Search versioned Markdown runbooks locally using validated metadata, aliases,
normalization, term matching, and deterministic scoring behind `KnowledgeSearch`.
No embeddings or vector database are used in V1.

## Consequences

The mechanism is transparent and offline but has limited semantic recall. Curated
aliases mitigate common synonyms; a future adapter can replace it.

