# ruff: noqa: E501, SIM117
"""Thin Streamlit presentation adapter for SupportOps V1."""

import streamlit as st
from pydantic import ValidationError

from supportops.bootstrap import build_application
from supportops.errors import SupportOpsError
from supportops.web_facade import IncidentFilters


def _safe_error(error: Exception) -> str:
    if isinstance(error, SupportOpsError):
        return error.public_message
    if isinstance(error, ValidationError):
        return "Revise os campos informados e tente novamente."
    return "A operação falhou com segurança. Tente novamente."


def _incident_selector(web: object) -> str | None:
    views = web.list_incidents()  # type: ignore[attr-defined]
    if not views:
        st.info("Nenhum incidente operacional disponível.")
        return None
    options: dict[str, str] = {
        f"{v.incident.title} — {v.incident.id}": str(v.incident.id) for v in views
    }
    selected = st.selectbox("Incidente", tuple(options))
    return options[selected]


def render() -> None:
    st.set_page_config(page_title="SupportOps Command Center", layout="wide")
    st.title("SupportOps Command Center")
    try:
        app = build_application()
        web = app.web
        status = web.bootstrap_database()
    except Exception as error:
        st.error(_safe_error(error))
        return
    render_with_facade(web, status)


def render_with_facade(web: object, status: object) -> None:
    """Render the presentation over an injected application facade."""
    st.caption(
        f"Banco v{status.current_version}; migrações pendentes: "  # type: ignore[attr-defined]
        f"{len(status.pending_versions)}"  # type: ignore[attr-defined]
    )
    page = st.sidebar.radio(
        "Área",
        (
            "Dashboard",
            "Incidentes",
            "Triagem",
            "Conhecimento",
            "Procedimentos e documentos",
        ),
    )
    try:
        if page == "Dashboard":
            _dashboard(web)
        elif page == "Incidentes":
            _incidents(web)
        elif page == "Triagem":
            _triage(web)
        elif page == "Conhecimento":
            _knowledge(web)
        else:
            _documents(web)
    except Exception as error:
        st.error(_safe_error(error))


def _dashboard(web: object) -> None:
    metrics = web.dashboard()  # type: ignore[attr-defined]
    columns = st.columns(4)
    columns[0].metric("Total de incidentes", metrics.total_incidents)
    columns[1].metric("Abertos", metrics.open_count)
    columns[2].metric("Encerrados", metrics.closed_count)
    columns[3].metric("Escalonamentos", metrics.escalation_count)
    st.metric(
        "Tempo médio de atendimento",
        "Sem dados"
        if metrics.mean_handling_seconds is None
        else f"{metrics.mean_handling_seconds:.0f} s",
    )
    st.subheader("Por prioridade")
    st.dataframe(dict(metrics.by_priority), use_container_width=True)
    st.subheader("Por categoria")
    st.dataframe(dict(metrics.by_category), use_container_width=True)
    st.caption(f"Snapshot: {metrics.calculated_at.isoformat()}")


def _incidents(web: object) -> None:
    st.header("Incidentes")
    with st.expander("Cadastrar incidente"):
        with st.form("create_incident", clear_on_submit=True):
            title = st.text_input("Título")
            description = st.text_area("Descrição")
            party = st.text_input("Parte afetada")
            service = st.text_input("Serviço afetado")
            impact = st.selectbox("Impacto", ("low", "moderate", "high", "critical"))
            urgency = st.selectbox("Urgência", ("low", "moderate", "high", "critical"))
            symptoms = st.text_area("Sintomas")
            category = st.text_input("Categoria")
            actor = st.text_input("Ator")
            if st.form_submit_button("Cadastrar"):
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
                st.success("Incidente cadastrado.")
    text = st.text_input("Filtrar texto")
    status = st.selectbox("Filtrar status", ("Todos", "OPEN", "CLOSED"))
    priority = st.selectbox("Filtrar prioridade", ("Todos", "P1", "P2", "P3", "P4"))
    category_filter = st.text_input("Filtrar categoria")
    filters = IncidentFilters(
        text=text or None,
        status=web.parse_status(status),  # type: ignore[attr-defined]
        priority=None if priority == "Todos" else priority,
        category=category_filter or None,
    )
    views = web.list_incidents(filters)  # type: ignore[attr-defined]
    if not views:
        st.info("Nenhum incidente encontrado.")
        return
    for view in views:
        st.subheader(view.incident.title)
        st.write(
            {
                "id": view.incident.id,
                "status": view.incident.status.value,
                "prioridade": view.priority,
                "categoria": view.category,
            }
        )
    incident_id = _incident_selector(web)
    if not incident_id:
        return
    view = web.get_incident(incident_id)  # type: ignore[attr-defined]
    st.write(view.incident.model_dump(mode="json"))
    with st.form("update_incident"):
        title = st.text_input("Novo título", value=view.incident.title)
        description = st.text_area("Nova descrição", value=view.incident.description)
        party = st.text_input("Nova parte afetada", value=view.incident.affected_party)
        service = st.text_input(
            "Novo serviço afetado", value=view.incident.affected_service
        )
        symptoms = st.text_area("Novos sintomas", value=view.incident.symptoms)
        category = st.text_input("Nova categoria", value=view.incident.category or "")
        actor = st.text_input("Ator da atualização")
        if st.form_submit_button("Atualizar"):
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
            st.success("Incidente atualizado.")
    c1, c2 = st.columns(2)
    if c1.button("Encerrar"):
        web.close_incident(incident_id, None)  # type: ignore[attr-defined]
        st.success("Incidente encerrado.")
    if c2.button("Reabrir"):
        web.reopen_incident(incident_id, None)  # type: ignore[attr-defined]
        st.success("Incidente reaberto.")
    with st.form("delete_incident"):
        reason = st.text_input("Motivo da exclusão lógica")
        confirmed = st.checkbox("Confirmo a exclusão lógica deste incidente")
        if st.form_submit_button("Excluir logicamente"):
            if not confirmed:
                st.warning("Confirme explicitamente a exclusão lógica.")
            else:
                web.delete_incident(incident_id, reason, confirmed, None)  # type: ignore[attr-defined]
                st.success("Incidente excluído logicamente.")
    st.subheader("Histórico imutável")
    for event in web.incident_history(incident_id):  # type: ignore[attr-defined]
        st.write(event.model_dump(mode="json"))


def _triage(web: object) -> None:
    st.header("Triagem determinística")
    incident_id = _incident_selector(web)
    if not incident_id:
        return
    selected = web.get_incident(incident_id)  # type: ignore[attr-defined]
    st.caption(f"Categoria persistida: {selected.incident.category or 'Não informada'}")
    with st.form("triage"):
        evidence_json = st.text_area("Evidências de triagem (JSON)", value="{}")
        actor = st.text_input("Ator da triagem")
        if st.form_submit_button("Executar triagem"):
            result = web.run_triage_json(incident_id, evidence_json, actor)  # type: ignore[attr-defined]
            st.session_state["triage_result"] = (incident_id, result)
    bound = st.session_state.get("triage_result")
    if bound is not None and bound[0] == incident_id:
        result = bound[1]
        st.write(f"Resultado: {result.outcome.value}")
        st.write(
            {
                "prioridade": result.priority.value if result.priority else None,
                "rota": result.recommended_route.value
                if result.recommended_route
                else None,
                "escalonamento": result.escalation_required,
                "razões": result.escalation_reason_ids,
                "evidências ausentes": result.missing_evidence,
            }
        )
        for question in result.questions:
            st.write(f"Pergunta: {question.question}")
    st.subheader("Histórico de triagem")
    for item in web.triage_history(incident_id):  # type: ignore[attr-defined]
        st.write(item.model_dump(mode="json"))


def _knowledge(web: object) -> None:
    st.header("Busca em runbooks")
    with st.form("knowledge_search"):
        query = st.text_input("Consulta")
        if st.form_submit_button("Buscar"):
            st.session_state["knowledge_results"] = (query, web.search_knowledge(query))  # type: ignore[attr-defined]
    bound = st.session_state.get("knowledge_results")
    results = bound[1] if bound is not None else ()
    if not results:
        st.info("Nenhuma correspondência encontrada.")
    for rank, item in enumerate(results, start=1):
        st.subheader(f"{rank}. {item.title}")
        st.write(
            {
                "score": item.score,
                "termos": item.matched_terms,
                "id": item.id,
                "categoria": item.category,
                "revisão": item.revision,
                "fonte": item.source_path,
            }
        )
        st.text(item.excerpt)


def _documents(web: object) -> None:
    st.header("Procedimentos realizados e documentação")
    st.info(
        "Procedimentos sugeridos são orientação; procedimentos realizados são relatos e nunca são executados por esta interface."
    )
    incident_id = _incident_selector(web)
    if not incident_id:
        return
    with st.form("performed"):
        description = st.text_area("Procedimento efetivamente realizado")
        result = st.text_area("Resultado observado")
        actor = st.text_input("Ator responsável")
        if st.form_submit_button("Registrar procedimento"):
            web.record_performed_fields(incident_id, description, result, actor)  # type: ignore[attr-defined]
            st.success(
                "Procedimento registrado como relato; nenhuma ação foi executada."
            )
    for item in web.performed_history(incident_id):  # type: ignore[attr-defined]
        st.write(item.model_dump(mode="json"))
    with st.form("generate_document"):
        actor = st.text_input("Ator gerador")
        if st.form_submit_button("Gerar nova revisão"):
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
                f"Baixar {fmt.upper()}",
                artifact.content,
                artifact.filename,
                artifact.media_type,
            )


if __name__ == "__main__":
    render()
