# Architecture Overview

Status: Proposed for Phase 2 approval  
System: SupportOps Command Center  
Architecture style: local modular monolith with ports and adapters

## Goals

The system assists N1 and N2 analysts from incident registration through safe
troubleshooting and technical documentation. It must operate locally without an
LLM, preserve an audit trail, and never execute suggested commands.

## Context and boundaries

The application owns incident records, deterministic triage, evidence gaps,
hypotheses, troubleshooting plans, runbook search, approval records,
documentation, exports, history, and operational metrics.

It does not own identity management, remote administration, execution of shell
commands, GLPI/ServiceNow integration, Microsoft 365 administration, or SLA pause
calculation in V1.

## Architectural principles

1. CLI First: every operational use case is available through the CLI before a
   Streamlit screen is accepted. Streamlit is a thin adapter.
2. Dependency direction: presentation -> application -> domain. Infrastructure
   implements domain/application ports; the domain imports no adapter.
3. Deterministic core: required behavior works with the null LLM provider.
4. Safe suggestions: commands are immutable content objects, not executable jobs.
5. Auditability: status changes, logical deletion, and human approvals are
   append-only events or records linked to the incident and exact proposed action.
6. Local isolation: product code and artifacts remain under this project root.

## Logical view

```text
CLI ------------------+
                      +--> Application services --> Domain policies/models
Streamlit ------------+              |                       |
                                     +--> ports <------------+
                                            |
                  +-------------------------+-----------------------+
                  |                         |                       |
           SQLite adapters          Markdown search          LLM provider
                                                         Null (default)/Ollama
```

## Planned modules

- `presentation.cli`: canonical operational interface.
- `presentation.streamlit`: local UI and observational dashboard.
- `application.use_cases`: commands and queries for the product workflow.
- `domain.models`: entities, value objects, enums, and invariants.
- `domain.policies`: priority, escalation, approval, and status policies.
- `domain.ports`: repository, knowledge, provider, clock, and exporter contracts.
- `infrastructure.persistence.sqlite`: repositories and versioned migrations.
- `infrastructure.knowledge.markdown`: lexical local search.
- `infrastructure.llm`: null, fake-test, and optional Ollama adapters.
- `infrastructure.configuration`: validated environment and matrix loading.
- `infrastructure.logging`: structured logging with sensitive-field redaction.

## Primary flow

1. Register and validate an incident.
2. Classify it using the versioned priority configuration.
3. Detect missing evidence and show diagnostic questions.
4. Search local runbooks and assemble traceable hypotheses.
5. Present a safe, ordered troubleshooting plan.
6. Record performed procedures and any human approval decision.
7. Generate technical documentation and persist the incident.
8. Query history, export, or view observational metrics.

## Security boundaries

- No shell-execution port or adapter will exist.
- Database statements use bound parameters and transactions.
- User-selected paths never reach filesystem APIs directly.
- Export and knowledge roots come from validated configuration.
- Errors shown to users omit stack traces, secrets, and full sensitive payloads.
- LLM input is minimized; output is untrusted and validated before use.
- Approval records authorize nothing automatically and cannot trigger execution.

## Runtime and deployment

Python 3.12 is the target runtime. The local process hosts CLI commands or the
Streamlit server. SQLite is stored at a configured path and later mounted as a
Docker volume. Ollama is an optional external local service and is not included
in the required startup path.

## Observability

Structured local logs will contain correlation/incident identifiers, operation,
severity, and safe error codes. Passwords, tokens, full incident descriptions,
command output, and approval notes are excluded or redacted.

## Quality gates

Each increment must provide its mapped tests and keep all earlier tests green.
CLI end-to-end evidence is required before Streamlit implementation. Security
findings rated critical block progress. Human approval is required between phases.

