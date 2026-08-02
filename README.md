# SupportOps Command Center

Local-first incident assistance for N1 and N2 support professionals.

## Current status

Phase 3, Increment 3 provides the Python 3.12 foundation, SQLite incident
lifecycle, and deterministic evidence-based triage through the canonical CLI.
The lifecycle remains strictly `OPEN ↔ CLOSED`. Triage uses the approved initial
V1 policy and is subject to future calibration with operational data. Runbooks,
Streamlit, LLM/network providers, exports, dashboard, restore, physical deletion,
and command execution remain absent.

## Install

```powershell
uv venv --python 3.12 .venv
uv sync --extra dev
.\.venv\Scripts\supportops.exe config validate
.\.venv\Scripts\supportops.exe db status
.\.venv\Scripts\supportops.exe db init
```

Configuration is optional and uses the `SUPPORTOPS_` prefix. See `.env.example`.
LLM is disabled. `db status` does not create or migrate a missing database;
`db init` applies ordered, checksummed migrations transactionally and is
idempotent.

## CLI lifecycle

```powershell
.\.venv\Scripts\supportops.exe incident create --title "Network" --description "No access" --affected-party "Finance" --affected-service "LAN" --impact moderate --urgency high --symptoms "Timeout"
.\.venv\Scripts\supportops.exe incident get INCIDENT_ID
.\.venv\Scripts\supportops.exe incident list
.\.venv\Scripts\supportops.exe incident update INCIDENT_ID --expected-version 1 --title "Updated"
.\.venv\Scripts\supportops.exe incident close INCIDENT_ID
.\.venv\Scripts\supportops.exe incident reopen INCIDENT_ID
.\.venv\Scripts\supportops.exe incident history INCIDENT_ID
.\.venv\Scripts\supportops.exe incident delete INCIDENT_ID --reason "duplicate" --confirm
```

Deletion is logical, irreversible in V1, and excluded from operational queries.
There is no restore or physical-delete command. Approval identity is user-declared
and not authenticated; approval only records exact action metadata and never
executes the action.

## CLI deterministic triage

Initialize the database and create an incident first. Triage accepts one JSON
object of structured evidence; free text never creates a risk signal. Use
`--format json` for machine-readable output.

```powershell
$evidence = '{"impact":"high","urgency":"high","supported_impact_criteria":["high"],"supported_urgency_criteria":["high"],"affected_scope":"Finance department","scope_source":"multiple tickets","affected_process":"shift processing","process_criticality":"important","workaround_status":"limited","workaround_validation":"tested","business_consequence":"significant delay","containment_status":"stable scope","critical_impact_reassessment":"critical expansion not supported","deadline":"current shift","deadline_owner":"finance lead","delay_consequence":"cutoff missed","time_to_harm":"within hours","condition_stability":"stable","failure_frequency":"continuous","trend":"stable","symptom_context":"timestamped timeout","prior_actions":"read-only checks","recent_change":"none","corroboration":"multiple tickets","risk_assessment_status":"none_identified","requires_admin_or_change":false,"within_approved_runbook_or_noninvasive":true,"n1_safe_boundary":true,"expected_result_defined":true,"stop_condition_defined":true}'
.\.venv\Scripts\supportops.exe triage run INCIDENT_ID --evidence-json $evidence
.\.venv\Scripts\supportops.exe triage run INCIDENT_ID --evidence-json $evidence --format json
.\.venv\Scripts\supportops.exe triage history INCIDENT_ID --format json
```

The default packaged policy is `supportops-triage`, schema `1`, matrix
`2026.08-v1`. A project-owned override may be selected with
`SUPPORTOPS_TRIAGE_POLICY_PATH`; invalid, incomplete, unsupported, or unreadable
policy configuration stops startup and never activates a fallback. Re-triage
appends a new immutable snapshot and never overwrites prior results.

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build
```

The application has no subprocess, shell, administrative executor, Streamlit,
network, or LLM adapter. SQL values are bound parameters and errors shown to the
operator omit SQL, database paths, sensitive payloads, and tracebacks.
