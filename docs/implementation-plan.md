# Incremental Implementation Plan

Status: Proposed. Execution is blocked until Phase 2 approval.

## Increment 0 — Architecture gate

Approve this package, complete the Support Specialist priority matrix/boundaries,
and resolve the decisions in `pending.md`.

## Increment 1 — Foundation and CLI skeleton

Create Python packaging, validated settings, domain primitives, safe errors,
composition root, empty/local provider contracts, CLI health/config commands, and
unit/contract/smoke tests. No Streamlit business flow.

## Increment 2 — SQLite and incident lifecycle

Create versioned migrations and repositories; implement registration, retrieval,
status history, closing/reopening, soft deletion, approval records, and CLI flows.
Run real SQLite integration and regression tests.

## Increment 3 — Deterministic triage and evidence

Implement the approved versioned priority matrix, category rules, escalation,
evidence-gap questions, hypotheses, and safe plan ordering. Prove via CLI.

## Increment 4 — Knowledge base

Write and review the five runbooks, implement local lexical search, containment
checks, source traceability, and five-scenario integration tests.

## Increment 5 — Documentation and export

Record performed procedures separately from suggestions; generate nine-section
documentation and safe Markdown/JSON exports. Verify against persisted data.

## Increment 6 — Streamlit, history, and dashboard

Add thin UI flows over existing services, confirmation for logical deletion,
filters, audit-aware views, and observational metrics. No direct SQLite access.

## Increment 7 — Optional Ollama

Implement the adapter, structured validation, timeout, health, and fallback.
Required tests remain fake/mock and offline.

## Increment 8 — Hardening and delivery

Complete regression/security review, Docker/Compose, clean-install README,
demonstration, evidence pack, progress/pending/file-list updates, and final gate.

## Per-increment protocol

1. Activate the story and confirm acceptance criteria.
2. Implement the smallest testable slice.
3. Run new tests and full applicable regression.
4. Fix failures before continuing.
5. Update story checklist, File List, progress, pending, decisions, and evidence.
6. Request the required human approval before crossing a main phase boundary.

