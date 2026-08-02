# Local knowledge runbook format

Each runbook is a regular UTF-8 `.md` file directly under the configured fixed
knowledge root. TOML front matter is delimited by `+++` and requires exactly the
typed fields `id`, `title`, `aliases`, `category`, `symptoms`, `keywords`,
`risk_notes`, `escalation_criteria`, and semantic `revision`. The Markdown body
is required and contains exactly one ordered, non-empty section for each heading:
`# Objetivo`, `## Evidências seguras`, `## Orientação não executável`, and
`## Pare e escale`. Missing, empty, duplicate, reordered, or additional headings
invalidate the corpus. No credentials or personal data are permitted.

The corpus is fail-closed: a missing root, malformed metadata, invalid UTF-8,
duplicate ID, unreadable file, symlink, resolved-path escape, empty corpus, or
unsupported document invalidates the request without returning partial results. Only direct,
regular `.md` children are considered; returned evidence contains only a file
name relative to the root.

## Deterministic lexical ranking

Query terms are Unicode NFKD-normalized, case-folded, stripped of combining
accents and punctuation, deduplicated, and sorted. Each unique term contributes
once per matching field: title 50, aliases 40, symptoms 30, keywords 25, and
content 10. Whole normalized tokens match; documents with no matching term are
excluded. Ordering is descending score, then normalized title, document ID, and
relative source path. Excerpts choose the earliest paragraph with the most
matched terms and are whitespace-normalized and capped at 240 characters.

This specification intentionally defines lexical equivalence only. Aliases and
keywords curate common synonyms; no embedding, LLM, network, dynamic execution,
template evaluation, shell command, or administrative action exists.
