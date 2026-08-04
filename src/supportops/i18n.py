"""English presentation strings for the Streamlit interface."""

from collections.abc import Mapping
from typing import Final, Literal

LanguageCode = Literal["en"]
DEFAULT_LANGUAGE: Final[LanguageCode] = "en"

CATALOGS: Final[Mapping[LanguageCode, Mapping[str, str]]] = {
    "en": {
        "db_status": "Database v{version}; pending migrations: {pending}",
        "area": "Area",
        "page_dashboard": "Dashboard",
        "page_incidents": "Incidents",
        "page_triage": "Triage",
        "page_knowledge": "Knowledge",
        "page_documents": "Procedures and documents",
        "validation_error": "Review the provided fields and try again.",
        "safe_error": "The operation failed safely. Try again.",
        "no_incidents": "No operational incidents are available.",
        "incident": "Incident",
        "metric_total": "Total incidents",
        "metric_open": "Open",
        "metric_closed": "Closed",
        "metric_escalations": "Escalations",
        "mean_handling_time": "Mean handling time",
        "no_data": "No data",
        "seconds": "{value:.0f} s",
        "by_priority": "By priority",
        "by_category": "By category",
        "snapshot": "Snapshot: {timestamp}",
        "register_incident": "Register incident",
        "title": "Title",
        "description": "Description",
        "affected_party": "Affected party",
        "affected_service": "Affected service",
        "impact": "Impact",
        "urgency": "Urgency",
        "symptoms": "Symptoms",
        "category": "Category",
        "actor": "Actor",
        "register": "Register",
        "incident_registered": "Incident registered.",
        "filter_text": "Filter text",
        "filter_status": "Filter status",
        "filter_priority": "Filter priority",
        "filter_category": "Filter category",
        "status_all": "All",
        "status_open": "OPEN",
        "status_closed": "CLOSED",
        "priority_all": "All",
        "no_incidents_found": "No incidents found.",
        "field_id": "id",
        "field_status": "status",
        "field_priority": "priority",
        "field_category": "category",
        "new_title": "New title",
        "new_description": "New description",
        "new_affected_party": "New affected party",
        "new_affected_service": "New affected service",
        "new_symptoms": "New symptoms",
        "new_category": "New category",
        "update_actor": "Update actor",
        "update": "Update",
        "incident_updated": "Incident updated.",
        "close": "Close",
        "reopen": "Reopen",
        "incident_closed": "Incident closed.",
        "incident_reopened": "Incident reopened.",
        "logical_delete_reason": "Logical deletion reason",
        "logical_delete_confirm": "I confirm the logical deletion of this incident",
        "logical_delete": "Logically delete",
        "logical_delete_warning": "Explicitly confirm the logical deletion.",
        "logical_delete_success": "Incident logically deleted.",
        "immutable_history": "Immutable history",
        "deterministic_triage": "Deterministic triage",
        "persisted_category": "Persisted category: {category}",
        "not_informed": "Not provided",
        "triage_evidence": "Triage evidence (JSON)",
        "triage_actor": "Triage actor",
        "run_triage": "Run triage",
        "result": "Result: {outcome}",
        "field_route": "route",
        "field_escalation": "escalation",
        "field_reasons": "reasons",
        "field_missing_evidence": "missing evidence",
        "question": "Question: {question}",
        "triage_history": "Triage history",
        "runbook_search": "Runbook search",
        "query": "Query",
        "search": "Search",
        "no_matches": "No matches found.",
        "field_score": "score",
        "field_terms": "terms",
        "field_revision": "revision",
        "field_source": "source",
        "performed_and_documentation": "Performed procedures and documentation",
        "procedure_safety_notice": (
            "Suggested procedures are guidance; performed procedures are operator "
            "records and are never executed by this interface."
        ),
        "performed_procedure": "Procedure actually performed",
        "observed_result": "Observed result",
        "responsible_actor": "Responsible actor",
        "record_procedure": "Record procedure",
        "procedure_recorded": (
            "Procedure recorded as an operator report; no action was executed."
        ),
        "generator_actor": "Generator actor",
        "generate_revision": "Generate new revision",
        "download": "Download {format}",
        "impact_low": "Low",
        "impact_moderate": "Moderate",
        "impact_high": "High",
        "impact_critical": "Critical",
    }
}


def translate(language: LanguageCode, key: str, **values: object) -> str:
    """Return one English interface message and fail fast for an unknown key."""
    try:
        template = CATALOGS[language][key]
    except KeyError as error:
        raise KeyError(f"Unknown localization key: {language}.{key}") from error
    return template.format(**values)


def catalog_keys(language: LanguageCode) -> frozenset[str]:
    """Expose catalog keys for presentation tests."""
    return frozenset(CATALOGS[language])
