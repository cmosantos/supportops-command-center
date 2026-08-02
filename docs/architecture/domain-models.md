# Domain Models

Status: Proposed

This document defines conceptual Pydantic models and invariants. It is not code.

## Shared value types

- `IncidentId`, `ApprovalId`, `ActionId`: generated opaque identifiers.
- `UtcTimestamp`: timezone-aware UTC instant.
- `ActorReference`: user-supplied display identifier; not authentication proof.
- `Impact`: `low | moderate | high | critical`.
- `Urgency`: `low | moderate | high | critical`.
- `Priority`: `P1 | P2 | P3 | P4`.
- `SupportLevel`: `N1 | N2`.
- `RiskLevel`: `low | medium | high | critical`.
- `IncidentStatus`: `open | in_progress | resolved | closed | reopened`.
- `ApprovalDecision`: `pending | approved | rejected`.

## Incident

Required intake fields:

- id, title, description, affected_party, affected_service;
- impact, urgency, symptoms, error_messages, actions_already_taken;
- status, created_at, updated_at.

Lifecycle/audit fields:

- closed_at (latest close instant), escalated, category, subcategory, priority;
- deleted_at, deletion_reason, deletion_confirmed, pre_deletion_status;
- created_by/updated_by where an actor reference is provided.

Invariants:

1. Title, description, affected party, service, impact, urgency, and symptoms are
   mandatory after normalization.
2. Password/token fields do not exist.
3. A deleted incident remains persisted and is excluded by default queries.
4. Logical deletion requires reason, explicit confirmation, deletion timestamp,
   and previous status. Physical deletion is not a V1 use case.
5. `closed_at` is the most recent successful transition to `closed`.

## IncidentStatusEvent

- id, incident_id, previous_status, new_status, changed_at, actor_reference,
  optional reason.

Events are append-only. Reopening and closing again adds events; it never rewrites
earlier transitions. Mean handling time uses latest `closed_at - created_at` for
currently closed, non-deleted incidents. Waiting/SLA pauses are not deducted in V1.

## TriageResult

- category, subcategory, impact, urgency, priority, recommended_support_level,
  escalation_required, rationale, priority_matrix_version, generated_at.

Priority is deterministic and linked to the exact validated matrix version.

## DiagnosticQuestion

- id, topic, question, required_evidence, reason, blocking_before_solution.

Questions already answered by supplied evidence are not repeated. Blocking
questions precede the troubleshooting solution.

## Hypothesis

- id, statement, justification, required_evidence, confidence,
  recommended_verification, discard_condition, source_references, status.

Confidence is bounded from 0 to 1 and is an aid, not a probability guarantee.

## TroubleshootingPlan and TroubleshootingStep

Plan fields: incident_id, generated_at, steps, escalation_criteria.

Step fields: id, sequence, phase, objective, instruction, expected_result,
risk_level, administrative_privilege_required, requires_human_approval,
rollback_procedure, source_references.

Phase order is fixed:

1. `non_invasive`
2. `configuration_check`
3. `controlled_test`
4. `corrective_action`
5. `escalation`

## CommandSuggestion

- action_id, version, command_text, objective, target_system, risk_level,
  administrative_privilege_required, expected_result, rollback_procedure,
  requires_human_approval.

It is display-only data. No execute method, executor service, or shell adapter is
part of the architecture. A stable action ID plus version binds approvals to the
exact suggestion and prevents reuse for a changed action.

## HumanApproval

- id, incident_id, action_id, action_version, action_digest, action_snapshot;
- decision/status, approver_reference, decided_at, optional note, created_at.

The approver reference is user-provided and provides operational traceability,
not verified authentication. Approval never causes command execution. A decision
is immutable; a new decision creates a new record.

## KnowledgeDocument and SearchResult

Implemented ST-04 document fields: id, title, aliases, category, symptoms,
keywords, risk_notes, escalation_criteria, root-contained relative source path,
content, and revision.

Search result fields: document metadata, lexical score, matched_terms, excerpt.
Resolved paths must remain inside the configured knowledge root.

Search results expose validated display metadata, integer lexical score, sorted
matched terms, deterministic excerpt, revision, and relative source file. The
canonical scoring and tie-break contract is documented in
`docs/support/knowledge-runbook-format.md`.

## IncidentDocumentation

- executive_summary, technical_description, collected_evidence,
  evaluated_hypotheses, performed_procedures, applied_solution, result,
  preventive_recommendation, ticket_ready_text.

Suggested procedures and performed procedures are separate collections.

## DashboardMetrics

- total_incidents, by_priority, by_category, open_count, closed_count,
  mean_handling_seconds, escalation_count, calculated_at.

Default metrics exclude logically deleted incidents. The audit view is separate.

ST-06 implements this as one application snapshot. Priority/category and
escalation values come from the latest persisted triage snapshot; handling time
uses the latest `closed_at - created_at` value of currently closed incidents.
Empty databases return zero counts, empty ordered groups, and `None` for mean
handling time.

## PriorityMatrixConfiguration

- schema_version, matrix_version, effective_from, impact_values, urgency_values,
  rules, fallback_behavior.

Invalid or incomplete configuration fails closed during startup with a safe,
actionable configuration error. It never silently applies ad-hoc defaults. The
initial complete matrix and boundary cases require Support Specialist approval
before implementation.


## ST-03 implemented triage models

`TriageEvidence` is a strict structured input. Impact and urgency remain optional
until supported; structured risk status is one of `not_assessed`,
`none_identified`, `suspected`, or `confirmed`, with a closed six-ID catalog and
validated status/ID pairing. Free text never changes risk status.

`TriageResult` is an immutable complete or incomplete snapshot with policy ID,
schema/matrix version, SHA-256 revision, normalized input, rule/rationale,
priority, route, additive escalation reasons, missing evidence, ordered diagnostic
questions, structured stop outcome, timestamp and declared actor. Incomplete
results cannot carry fabricated priority or support route. Re-triage creates a new
snapshot with the next sequence.
