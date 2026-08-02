# Usage Guide

## Database and incidents

Run `supportops db status`, then `supportops db init`. Use `incident create`,
`get`, `list`, `update --expected-version`, `close`, `reopen`, `history`, and
`delete --reason ... --confirm`. Deletion is logical, excluded from operations,
and cannot be restored in V1.

## Triage and knowledge

`triage run INCIDENT_ID --evidence-json JSON` stores an immutable deterministic
snapshot with priority, route, escalation, diagnostic questions and evidence gaps.
`triage history` displays snapshots. `knowledge search QUERY --format json`
searches title, aliases, symptoms, keywords and content using accent-insensitive
lexical ranking; no result is valid and exits `0`.

## Performed work and documentation

`performed record` stores only a user-reported procedure and result. Suggested
procedures never become performed automatically and nothing is executed. Use
`performed list`, `document generate`, `document show` and `document history`.
Each revision contains: executive summary, technical description, evidence,
hypotheses, suggestions, performed procedures, solution, result/prevention, and
GLPI/ServiceNow-ready text.

## Exports

`export INCIDENT_ID --revision N --format markdown|json` safely publishes a new
opaque name under the configured root. Existing files are never overwritten.
JSON output is strict schema version 1. Markdown preserves the nine headings.

## Streamlit and dashboard

Run `uv run streamlit run src/supportops/streamlit_app.py`. The sidebar exposes
database, incidents/history, triage, knowledge, documentation/export and dashboard
flows. Dashboard totals, priority/category groups, open/closed counts, mean handling
time and escalation count are observational; logically deleted incidents are absent.

## Exit behavior

Success (including zero search matches) exits `0`; validation/safe domain failures
exit `2`; unexpected safely masked failures exit `1`. The UI shows safe messages
without SQL, local paths, payloads or tracebacks.
