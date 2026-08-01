# Contracts and Interfaces

Status: Proposed; signatures are conceptual.

## Application use cases

- `RegisterIncident(input) -> Incident`
- `ClassifyIncident(incident_id) -> TriageResult`
- `IdentifyEvidenceGaps(incident_id) -> list[DiagnosticQuestion]`
- `BuildHypothesisTree(incident_id) -> list[Hypothesis]`
- `BuildTroubleshootingPlan(incident_id) -> TroubleshootingPlan`
- `SearchKnowledge(query) -> list[SearchResult]`
- `RecordApproval(input) -> HumanApproval`
- `RecordPerformedProcedure(input) -> PerformedProcedure`
- `GenerateIncidentDocumentation(incident_id) -> IncidentDocumentation`
- `CloseIncident`, `ReopenIncident`, `SoftDeleteIncident`
- `ListIncidents(filters)`, `GetDashboardMetrics()`
- `ExportIncident(incident_id, format) -> ExportArtifact`

Commands mutate state and run transactionally. Queries do not mutate state.

## Ports

### `IncidentRepository`

Create/get/update, filtered list, append status event, soft-delete transaction,
audit retrieval, and metric queries. Normal methods exclude deleted incidents.

### `AnalysisRepository`

Stores immutable triage snapshots, questions, hypotheses, plans, suggestions,
performed-procedure reports, approvals, and documentation revisions.

### `KnowledgeSearch`

`search(query, limit)`, `get(document_id)`, and `health()` over documents rooted
inside the configured knowledge directory.

### `PriorityPolicy`

Loads one validated versioned configuration and calculates a priority with an
explanation. Invalid configuration returns a configuration error; no silent
fallback matrix is allowed.

### `LLMProvider`

`is_enabled`, `complete_structured(request, response_schema, timeout)`, `health`.

Implementations:

- `NullLLMProvider`: disabled/default and deterministic fallback signal.
- `OllamaLLMProvider`: optional HTTP adapter.
- `FakeLLMProvider`: injectable test adapter for success, timeout, invalid output,
  and unavailability. Mandatory tests never require a real Ollama server.

All provider output is untrusted and Pydantic-validated. Failure returns a typed
provider error and invokes the documented local fallback.

### `IncidentExporter`

Produces bytes/text plus safe media type and generated filename. Adapters are
Markdown and JSON. The export root is configured; callers cannot provide paths.

### `Clock`, `IdGenerator`, `UnitOfWork`, `AuditLogger`

Injectable system boundaries support deterministic tests, atomic writes, and
safe operational records.

## Error contract

- `ValidationError`: safe field-level feedback.
- `NotFoundError`: absent or normally hidden entity.
- `InvalidTransitionError`: disallowed lifecycle transition.
- `ConfigurationError`: invalid matrix/environment configuration.
- `PersistenceError`: safe operation code, original detail only in redacted log.
- `KnowledgeError`, `ProviderError`, `ExportError`.

Presentation adapters map these errors to stable exit codes or safe UI messages.

## CLI contract

Planned command groups: `incident`, `triage`, `knowledge`, `approval`, `document`,
`export`, and `dashboard`. Machine-readable JSON output will be available where
needed for testing. The CLI contains no domain rules.

## Streamlit contract

Streamlit calls application services through the same composition root used by
the CLI. It does not access SQLite directly, calculate priority, parse runbooks,
or call Ollama directly. Dashboard screens are observational.

## Approval contract

Approval input must identify the incident, exact action ID/version/digest,
decision, approver reference, and optional note. The service records a snapshot,
timestamp from `Clock`, and immutable decision. It returns no execution token and
has no connection to an executor.

## Configuration contract

Environment variables select fixed application-owned roots and provider options.
Configuration is validated at startup. Secrets are neither required for the base
application nor accepted in incident models. `.env.example` contains placeholders
only; a real `.env` is ignored by Git.

