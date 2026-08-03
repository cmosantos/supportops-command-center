# ruff: noqa: E501, SIM117
"""Thin English Streamlit presentation adapter for SupportOps V1."""

import streamlit as st
from pydantic import ValidationError

from supportops.bootstrap import build_application
from supportops.errors import SupportOpsError
from supportops.i18n import DEFAULT_LANGUAGE, LanguageCode, translate
from supportops.web_facade import IncidentFilters

PRODUCTION_LANGUAGE: LanguageCode = "en"


def _safe_error(
    error: Exception, language: LanguageCode = DEFAULT_LANGUAGE
) -> str:
    if isinstance(error, SupportOpsError):
        return error.public_message
    if isinstance(error, ValidationError):
        return translate(language, "validation_error")
    return translate(language, "safe_error")


def _incident_selector(web: object, language: LanguageCode) -> str | None:
    views = web.list_incidents()  # type: ignore[attr-defined]
    if not views:
        st.info(translate(language, "no_incidents"))
        return None
    options: dict[str, str] = {
        f"{v.incident.title} — {v.incident.id}": str(v.incident.id) for v in views
    }
    selected = st.selectbox(translate(language, "incident"), tuple(options))
    return options[selected]


def _severity_label(value: str, language: LanguageCode) -> str:
    return translate(language, f"impact_{value}")


def render() -> None:
    st.set_page_config(page_title="SupportOps Command Center", layout="wide")
    st.title("SupportOps Command Center")
    try:
        app = build_application()
        web = app.web
        status = web.bootstrap_database()
    except Exception as error:
        st.error(_safe_error(error, PRODUCTION_LANGUAGE))
        return
    render_with_facade(web, status, language=PRODUCTION_LANGUAGE)


def render_with_facade(
    web: object,
    status: object,
    language: LanguageCode = DEFAULT_LANGUAGE,
) -> None:
    """Render the presentation over an injected application facade."""
    st.caption(
        translate(
            language,
            "db_status",
            version=status.current_version,  # type: ignore[attr-defined]
            pending=len(status.pending_versions),  # type: ignore[attr-defined]
        )
    )
    pages = {
        "dashboard": translate(language, "page_dashboard"),
        "incidents": translate(language, "page_incidents"),
        "triage": translate(language, "page_triage"),
        "knowledge": translate(language, "page_knowledge"),
        "documents": translate(language, "page_documents"),
    }
    page_keys = tuple(pages)
    current_page = st.session_state.get("supportops_current_page", "dashboard")
    if current_page not in pages:
        current_page = "dashboard"
    selected_page = st.sidebar.radio(
        translate(language, "area"),
        tuple(pages.values()),
        index=page_keys.index(current_page),
    )
    page = next(key for key, label in pages.items() if label == selected_page)
    st.session_state["supportops_current_page"] = page
    try:
        if page == "dashboard":
            _dashboard(web, language)
        elif page == "incidents":
            _incidents(web, language)
        elif page == "triage":
            _triage(web, language)
        elif page == "knowledge":
            _knowledge(web, language)
        else:
            _documents(web, language)
    except Exception as error:
        st.error(_safe_error(error, language))


def _dashboard(web: object, language: LanguageCode) -> None:
    metrics = web.dashboard()  # type: ignore[attr-defined]
    columns = st.columns(4)
    columns[0].metric(translate(language, "metric_total"), metrics.total_incidents)
    columns[1].metric(translate(language, "metric_open"), metrics.open_count)
    columns[2].metric(translate(language, "metric_closed"), metrics.closed_count)
    columns[3].metric(
        translate(language, "metric_escalations"), metrics.escalation_count
    )
    st.metric(
        translate(language, "mean_handling_time"),
        translate(language, "no_data")
        if metrics.mean_handling_seconds is None
        else translate(
            language, "seconds", value=metrics.mean_handling_seconds
        ),
    )
    st.subheader(translate(language, "by_priority"))
    st.dataframe(dict(metrics.by_priority), use_container_width=True)
    st.subheader(translate(language, "by_category"))
    st.dataframe(dict(metrics.by_category), use_container_width=True)
    st.caption(
        translate(
            language,
            "snapshot",
            timestamp=metrics.calculated_at.isoformat(),
        )
    )


def _incidents(web: object, language: LanguageCode) -> None:
    st.header(translate(language, "page_incidents"))
    with st.expander(translate(language, "register_incident")):
        with st.form("create_incident", clear_on_submit=True):
            title = st.text_input(translate(language, "title"))
            description = st.text_area(translate(language, "description"))
            party = st.text_input(translate(language, "affected_party"))
            service = st.text_input(translate(language, "affected_service"))
            impact = st.selectbox(
                translate(language, "impact"),
                ("low", "moderate", "high", "critical"),
                format_func=lambda value: _severity_label(value, language),
            )
            urgency = st.selectbox(
                translate(language, "urgency"),
                ("low", "moderate", "high", "critical"),
                format_func=lambda value: _severity_label(value, language),
            )
            symptoms = st.text_area(translate(language, "symptoms"))
            category = st.text_input(translate(language, "category"))
            actor = st.text_input(translate(language, "actor"))
            if st.form_submit_button(translate(language, "register")):
                web.create_from_fields(  # type: ignore[attr-defined]
                    title,
                    description,
                    party,
                    service,
                    impact,
                    urgency,
                    symptoms,
                    actor,
                    category,
                )
                st.success(translate(language, "incident_registered"))
    text = st.text_input(translate(language, "filter_text"))
    status_options = ("ALL", "OPEN", "CLOSED")
    status = st.selectbox(
        translate(language, "filter_status"),
        status_options,
        format_func=lambda value: translate(language, f"status_{value.lower()}"),
    )
    priority = st.selectbox(
        translate(language, "filter_priority"),
        ("ALL", "P1", "P2", "P3", "P4"),
        format_func=lambda value: (
            translate(language, "priority_all") if value == "ALL" else value
        ),
    )
    category_filter = st.text_input(translate(language, "filter_category"))
    filters = IncidentFilters(
        text=text or None,
        status=web.parse_status("Todos" if status == "ALL" else status),  # type: ignore[attr-defined]
        priority=None if priority == "ALL" else priority,
        category=category_filter or None,
    )
    views = web.list_incidents(filters)  # type: ignore[attr-defined]
    if not views:
        st.info(translate(language, "no_incidents_found"))
        return
    for view in views:
        st.subheader(view.incident.title)
        st.write(
            {
                translate(language, "field_id"): view.incident.id,
                translate(language, "field_status"): view.incident.status.value,
                translate(language, "field_priority"): view.priority,
                translate(language, "field_category"): view.category,
            }
        )
    incident_id = _incident_selector(web, language)
    if not incident_id:
        return
    view = web.get_incident(incident_id)  # type: ignore[attr-defined]
    st.write(view.incident.model_dump(mode="json"))
    with st.form("update_incident"):
        title = st.text_input(
            translate(language, "new_title"), value=view.incident.title
        )
        description = st.text_area(
            translate(language, "new_description"),
            value=view.incident.description,
        )
        party = st.text_input(
            translate(language, "new_affected_party"),
            value=view.incident.affected_party,
        )
        service = st.text_input(
            translate(language, "new_affected_service"),
            value=view.incident.affected_service,
        )
        symptoms = st.text_area(
            translate(language, "new_symptoms"),
            value=view.incident.symptoms,
        )
        category = st.text_input(
            translate(language, "new_category"),
            value=view.incident.category or "",
        )
        actor = st.text_input(translate(language, "update_actor"))
        if st.form_submit_button(translate(language, "update")):
            web.update_from_fields(  # type: ignore[attr-defined]
                incident_id,
                view.incident.version,
                title,
                description,
                party,
                service,
                symptoms,
                category,
                actor,
            )
            st.success(translate(language, "incident_updated"))
    c1, c2 = st.columns(2)
    if c1.button(translate(language, "close")):
        web.close_incident(incident_id, None)  # type: ignore[attr-defined]
        st.success(translate(language, "incident_closed"))
    if c2.button(translate(language, "reopen")):
        web.reopen_incident(incident_id, None)  # type: ignore[attr-defined]
        st.success(translate(language, "incident_reopened"))
    with st.form("delete_incident"):
        reason = st.text_input(translate(language, "logical_delete_reason"))
        confirmed = st.checkbox(translate(language, "logical_delete_confirm"))
        if st.form_submit_button(translate(language, "logical_delete")):
            if not confirmed:
                st.warning(translate(language, "logical_delete_warning"))
            else:
                web.delete_incident(incident_id, reason, confirmed, None)  # type: ignore[attr-defined]
                st.success(translate(language, "logical_delete_success"))
    st.subheader(translate(language, "immutable_history"))
    for event in web.incident_history(incident_id):  # type: ignore[attr-defined]
        st.write(event.model_dump(mode="json"))


def _triage(web: object, language: LanguageCode) -> None:
    st.header(translate(language, "deterministic_triage"))
    incident_id = _incident_selector(web, language)
    if not incident_id:
        return
    selected = web.get_incident(incident_id)  # type: ignore[attr-defined]
    st.caption(
        translate(
            language,
            "persisted_category",
            category=selected.incident.category
            or translate(language, "not_informed"),
        )
    )
    with st.form("triage"):
        evidence_json = st.text_area(
            translate(language, "triage_evidence"), value="{}"
        )
        actor = st.text_input(translate(language, "triage_actor"))
        if st.form_submit_button(translate(language, "run_triage")):
            result = web.run_triage_json(incident_id, evidence_json, actor)  # type: ignore[attr-defined]
            st.session_state["triage_result"] = (incident_id, result)
    bound = st.session_state.get("triage_result")
    if bound is not None and bound[0] == incident_id:
        result = bound[1]
        st.write(
            translate(language, "result", outcome=result.outcome.value)
        )
        st.write(
            {
                translate(language, "field_priority"): result.priority.value
                if result.priority
                else None,
                translate(language, "field_route"): result.recommended_route.value
                if result.recommended_route
                else None,
                translate(
                    language, "field_escalation"
                ): result.escalation_required,
                translate(language, "field_reasons"): result.escalation_reason_ids,
                translate(
                    language, "field_missing_evidence"
                ): result.missing_evidence,
            }
        )
        for question in result.questions:
            st.write(
                translate(language, "question", question=question.question)
            )
    st.subheader(translate(language, "triage_history"))
    for item in web.triage_history(incident_id):  # type: ignore[attr-defined]
        st.write(item.model_dump(mode="json"))


def _knowledge(web: object, language: LanguageCode) -> None:
    st.header(translate(language, "runbook_search"))
    with st.form("knowledge_search"):
        query = st.text_input(translate(language, "query"))
        if st.form_submit_button(translate(language, "search")):
            st.session_state["knowledge_results"] = (
                query,
                web.search_knowledge(query),  # type: ignore[attr-defined]
            )
    bound = st.session_state.get("knowledge_results")
    results = bound[1] if bound is not None else ()
    if not results:
        st.info(translate(language, "no_matches"))
    for rank, item in enumerate(results, start=1):
        st.subheader(f"{rank}. {item.title}")
        st.write(
            {
                translate(language, "field_score"): item.score,
                translate(language, "field_terms"): item.matched_terms,
                translate(language, "field_id"): item.id,
                translate(language, "field_category"): item.category,
                translate(language, "field_revision"): item.revision,
                translate(language, "field_source"): item.source_path,
            }
        )
        st.text(item.excerpt)


def _documents(web: object, language: LanguageCode) -> None:
    st.header(translate(language, "performed_and_documentation"))
    st.info(translate(language, "procedure_safety_notice"))
    incident_id = _incident_selector(web, language)
    if not incident_id:
        return
    with st.form("performed"):
        description = st.text_area(
            translate(language, "performed_procedure")
        )
        result = st.text_area(translate(language, "observed_result"))
        actor = st.text_input(translate(language, "responsible_actor"))
        if st.form_submit_button(translate(language, "record_procedure")):
            web.record_performed_fields(incident_id, description, result, actor)  # type: ignore[attr-defined]
            st.success(translate(language, "procedure_recorded"))
    for item in web.performed_history(incident_id):  # type: ignore[attr-defined]
        st.write(item.model_dump(mode="json"))
    with st.form("generate_document"):
        actor = st.text_input(translate(language, "generator_actor"))
        if st.form_submit_button(translate(language, "generate_revision")):
            document = web.generate_documentation(incident_id, actor)  # type: ignore[attr-defined]
            st.session_state["document"] = (incident_id, document)
    bound = st.session_state.get("document")
    document = bound[1] if bound is not None and bound[0] == incident_id else None
    if document is None:
        history = web.documentation_history(incident_id)  # type: ignore[attr-defined]
        document = history[-1] if history else None
    if document is not None:
        st.write(document.sections.model_dump(mode="json"))
        for fmt in ("markdown", "json"):
            artifact = web.export_content_name(incident_id, fmt, document.revision)  # type: ignore[attr-defined]
            st.download_button(
                translate(language, "download", format=fmt.upper()),
                artifact.content,
                artifact.filename,
                artifact.media_type,
            )


if __name__ == "__main__":
    render()
