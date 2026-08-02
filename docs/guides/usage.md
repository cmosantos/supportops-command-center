# Usage Guide

## Database and incidents

Run `supportops db status`, then `supportops db init`. Use `incident create`, `get`, `list`, `update --expected-version`, `close`, `reopen`, `history`, and `delete --reason ... --confirm`. Deletion is logical, excluded from operations, and cannot be restored in V1.

## Triage and knowledge

`triage run INCIDENT_ID --evidence-json JSON` stores an immutable deterministic snapshot with priority, route, escalation, diagnostic questions, and evidence gaps. `triage history` displays snapshots. `knowledge search QUERY --format json` searches title, aliases, symptoms, keywords, and content using accent-insensitive lexical ranking; no result is valid and exits `0`.

The Streamlit V1 triage screen accepts a raw JSON object. Field names must match the `TriageEvidence` schema exactly; unknown fields are rejected. Schema validation failures are currently reported with a generic safe message.

A complete synthetic evidence object can be based on this shape:

```json
{
  "impact": "moderate",
  "urgency": "moderate",
  "supported_impact_criteria": ["moderate"],
  "supported_urgency_criteria": ["moderate"],
  "affected_scope": "one synthetic user",
  "scope_source": "service desk interview",
  "affected_process": "shared mailbox access",
  "process_criticality": "important but not critical",
  "workaround_status": "web access available",
  "workaround_validation": "tested with synthetic account",
  "business_consequence": "mailbox work delayed",
  "containment_status": "single-user scope",
  "critical_impact_reassessment": "critical expansion not supported",
  "deadline": "current business day",
  "deadline_owner": "synthetic team lead",
  "delay_consequence": "processing delay",
  "time_to_harm": "within one business day",
  "condition_stability": "stable",
  "failure_frequency": "continuous",
  "trend": "stable",
  "symptom_context": "access denied in Outlook",
  "prior_actions": "read-only checks recorded",
  "recent_change": "permission state reviewed",
  "corroboration": "no related alerts",
  "risk_assessment_status": "none_identified",
  "requires_admin_or_change": false,
  "within_approved_runbook_or_noninvasive": true,
  "n1_safe_boundary": true,
  "expected_result_defined": true,
  "stop_condition_defined": true
}
```

Use synthetic evidence only. The policy is fail-closed: incomplete evidence produces diagnostic questions rather than a fabricated priority.

## Performed work and documentation

`performed record` stores only a user-reported procedure and result. Suggested procedures never become performed automatically and nothing is executed. Use `performed list`, `document generate`, `document show`, and `document history`. Each revision contains: executive summary, technical description, evidence, hypotheses, suggestions, performed procedures, solution, result/prevention, and GLPI/ServiceNow-ready text.

## Exports

`export INCIDENT_ID --revision N --format markdown|json` safely publishes a new opaque name under the configured root. Existing files are never overwritten. JSON output is strict schema version 1. Markdown preserves the nine headings.

## Streamlit and dashboard

Run `uv run streamlit run src/supportops/streamlit_app.py`. The sidebar exposes database, incidents/history, triage, knowledge, documentation/export, and dashboard flows. Dashboard totals, priority/category groups, open/closed counts, mean handling time, and escalation count are observational; logically deleted incidents are absent.

## Exit behavior

Success (including zero search matches) exits `0`; validation/safe domain failures exit `2`; unexpected safely masked failures exit `1`. The UI shows safe messages without SQL, local paths, payloads, or tracebacks.
