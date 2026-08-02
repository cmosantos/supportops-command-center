# ruff: noqa: E501
"""Interaction coverage for the thin Streamlit adapter over an injected facade."""

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from streamlit.testing.v1 import AppTest

from supportops.web_facade import DatabaseStatus, IncidentFilters


class Model(SimpleNamespace):
    def model_dump(self, **_: object) -> dict[str, object]:
        return dict(self.__dict__)


def incident(ident: str, title: str = "Caso", status: str = "OPEN") -> Model:
    return Model(
        id=ident,
        title=title,
        description="Descrição",
        affected_party="Pessoa",
        affected_service="Serviço",
        impact="low",
        urgency="low",
        symptoms="Sintoma",
        category="categoria",
        status=Model(value=status),
        version=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        closed_at=None,
        created_by="ator",
    )


class FakeFacade:
    def __init__(self) -> None:
        self.views: list[Model] = []
        self.calls: list[str] = []
        self.last_filters: object | None = None
        self.filter_calls: list[object] = []
        self.update_args: tuple[object, ...] = ()

    def dashboard(self) -> Model:
        return Model(
            total_incidents=len(self.views),
            by_priority=(),
            by_category=(),
            open_count=len(self.views),
            closed_count=0,
            mean_handling_seconds=None,
            escalation_count=0,
            calculated_at=datetime.now(UTC),
        )

    def list_incidents(self, filters: object = None) -> tuple[Model, ...]:
        self.last_filters = filters
        if filters is not None:
            self.filter_calls.append(filters)
        if filters is not None and getattr(filters, "text", None) == "missing":
            return ()
        return tuple(self.views)

    def parse_status(self, value: str) -> None:
        return None

    def create_from_fields(self, *args: str) -> Model:
        self.calls.append("create")
        view = Model(
            incident=incident("I-1", args[0]),
            priority="P4",
            category=args[-1] or None,
            escalated=False,
        )
        self.views.append(view)
        return view

    def get_incident(self, ident: str) -> Model:
        return next(view for view in self.views if view.incident.id == ident)

    def update_from_fields(self, *args: object) -> Model:
        self.calls.append("update")
        self.update_args = args
        return self.views[0]

    def close_incident(self, *args: object) -> Model:
        self.calls.append("close")
        return self.views[0]

    def reopen_incident(self, *args: object) -> Model:
        self.calls.append("reopen")
        return self.views[0]

    def delete_incident(self, *args: object) -> None:
        self.calls.append("delete")

    def incident_history(self, ident: str) -> tuple[Model, ...]:
        return (
            Model(
                event_type="INCIDENT_CREATED",
                actor_reference="ator",
                occurred_at=datetime.now(UTC),
                model_dump=lambda **_: {"event_type": "INCIDENT_CREATED"},
            ),
        )

    def run_triage_json(self, ident: str, payload: str, actor: str) -> Model:
        self.calls.append("triage")
        complete = payload != "{}"
        return Model(
            outcome=Model(value="triage_complete" if complete else "triage_incomplete"),
            priority=Model(value="P1") if complete else None,
            recommended_route=Model(value="N2") if complete else None,
            escalation_required=complete,
            escalation_reason_ids=("risk",) if complete else (),
            missing_evidence=() if complete else ("impact",),
            questions=(Model(question="Qual o impacto?"),),
            model_dump=lambda **_: {},
        )

    def triage_history(self, ident: str) -> tuple[Model, ...]:
        return ()

    def search_knowledge(self, query: str) -> tuple[Model, ...]:
        self.calls.append("search")
        if query == "none":
            return ()
        if query == "error":
            raise ValueError("hostile secret path")
        return (
            Model(
                id="rb",
                title="Runbook",
                category="network",
                score=90,
                matched_terms=("rede",),
                excerpt="Evidência",
                revision="1.0.0",
                source_path="runbook.md",
            ),
        )

    def record_performed_fields(self, *args: str) -> Model:
        self.calls.append("performed")
        return Model()

    def performed_history(self, ident: str) -> tuple[Model, ...]:
        return ()

    def generate_documentation(self, ident: str, actor: str) -> Model:
        self.calls.append("document")
        sections = Model(
            **{
                name: "conteúdo"
                for name in (
                    "executive_summary",
                    "technical_description",
                    "collected_evidence",
                    "evaluated_hypotheses",
                    "suggested_procedures",
                    "performed_procedures",
                    "applied_solution",
                    "result_and_preventive_recommendation",
                    "ticket_ready_text",
                )
            }
        )
        return Model(incident_id=ident, revision=1, sections=sections)

    def documentation_history(self, ident: str) -> tuple[Model, ...]:
        return ()

    def export_content_name(self, ident: str, fmt: str, revision: int) -> Model:
        return Model(
            content=b"content",
            filename=f"safe.{'md' if fmt == 'markdown' else 'json'}",
            media_type="text/plain",
        )


def injected_entry(web: object, status: object) -> None:
    from supportops.streamlit_app import render_with_facade

    render_with_facade(web, status)


def app(fake: FakeFacade) -> AppTest:
    return AppTest.from_function(
        injected_entry, args=(fake, DatabaseStatus(4, (), 0)), default_timeout=10
    ).run()


def widget(items: object, label: str) -> Any:
    return next(item for item in items if item.label == label)  # type: ignore[attr-defined]


def test_dashboard_empty_and_incident_create_rerun_is_idempotent() -> None:
    fake = FakeFacade()
    at = app(fake)
    assert [metric.value for metric in at.metric][:4] == ["0", "0", "0", "0"]
    at.sidebar.radio[0].set_value("Incidentes").run()
    widget(at.text_input, "Título").set_value("Novo")
    widget(at.text_input, "Parte afetada").set_value("Pessoa")
    widget(at.text_input, "Serviço afetado").set_value("Rede")
    widget(at.text_area, "Descrição").set_value("Descrição")
    widget(at.text_area, "Sintomas").set_value("Sintoma")
    widget(at.button, "Cadastrar").click().run()
    assert fake.calls.count("create") == 1
    at.run()
    assert fake.calls.count("create") == 1


def test_incident_filters_update_transitions_delete_and_history() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Caso", "", "", "", "", "", "", "", "categoria")
    at = app(fake)
    at.sidebar.radio[0].set_value("Incidentes").run()
    assert widget(at.selectbox, "Filtrar prioridade")
    assert widget(at.text_input, "Filtrar categoria")
    widget(at.text_input, "Filtrar texto").set_value("missing").run()
    assert any(info.value == "Nenhum incidente encontrado." for info in at.info)
    widget(at.text_input, "Filtrar texto").set_value("").run()
    widget(at.text_input, "Novo título").set_value("Atualizado")
    widget(at.button, "Atualizar").click().run()
    assert fake.update_args[2] == "Atualizado"
    assert fake.update_args[3:8] == (
        "Descrição",
        "Pessoa",
        "Serviço",
        "Sintoma",
        "categoria",
    )
    at.run()
    assert fake.calls.count("update") == 1
    widget(at.button, "Encerrar").click().run()
    widget(at.button, "Reabrir").click().run()
    assert {"update", "close", "reopen"}.issubset(fake.calls)
    at.run()
    assert fake.calls.count("close") == fake.calls.count("reopen") == 1
    widget(at.text_input, "Motivo da exclusão lógica").set_value("duplicado")
    widget(at.button, "Excluir logicamente").click().run()
    assert "delete" not in fake.calls
    widget(at.checkbox, "Confirmo a exclusão lógica deste incidente").check()
    widget(at.button, "Excluir logicamente").click().run()
    assert "delete" in fake.calls
    at.run()
    assert fake.calls.count("delete") == 1
    assert any("INCIDENT_CREATED" in str(value.value) for value in at.json)


def test_triage_and_knowledge_states_and_safe_errors() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Caso", "", "", "", "", "", "", "", "cat")
    at = app(fake)
    at.sidebar.radio[0].set_value("Triagem").run()
    widget(at.button, "Executar triagem").click().run()
    assert any("triage_incomplete" in item.value for item in at.markdown)
    widget(at.text_area, "Evidências de triagem (JSON)").set_value(
        '{"impact":"critical","urgency":"critical"}'
    )
    widget(at.button, "Executar triagem").click().run()
    assert any("Pergunta:" in item.value for item in at.markdown)
    at.run()
    assert fake.calls.count("triage") == 2
    at.sidebar.radio[0].set_value("Conhecimento").run()
    widget(at.text_input, "Consulta").set_value("rede")
    widget(at.button, "Buscar").click().run()
    assert any("1. Runbook" in item.value for item in at.subheader)
    assert any(text.value == "Evidência" for text in at.text)
    widget(at.text_input, "Consulta").set_value("none")
    widget(at.button, "Buscar").click().run()
    assert any(info.value == "Nenhuma correspondência encontrada." for info in at.info)
    widget(at.text_input, "Consulta").set_value("error")
    widget(at.button, "Buscar").click().run()
    assert any(
        error.value == "A operação falhou com segurança. Tente novamente."
        for error in at.error
    )


def test_performed_document_nine_sections_and_two_downloads() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Caso", "", "", "", "", "", "", "", "cat")
    at = app(fake)
    at.sidebar.radio[0].set_value("Procedimentos e documentos").run()
    widget(at.text_area, "Procedimento efetivamente realizado").set_value("Teste")
    widget(at.text_area, "Resultado observado").set_value("OK")
    inputs = [item for item in at.text_input if item.label == "Ator responsável"]
    inputs[0].set_value("analista")
    widget(at.button, "Registrar procedimento").click().run()
    widget(at.text_input, "Ator gerador").set_value("analista")
    widget(at.button, "Gerar nova revisão").click().run()
    assert fake.calls.count("performed") == fake.calls.count("document") == 1
    at.run()
    assert fake.calls.count("performed") == fake.calls.count("document") == 1
    assert len(at.download_button) == 2
    assert {item.label for item in at.download_button} == {
        "Baixar MARKDOWN",
        "Baixar JSON",
    }
    assert "executive_summary" in str(at.json[-1].value)


def test_priority_category_filters_are_passed_to_facade() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Caso", "", "", "", "", "", "", "", "cat")
    at = app(fake)
    at.sidebar.radio[0].set_value("Incidentes").run()
    widget(at.selectbox, "Filtrar prioridade").set_value("P2")
    widget(at.text_input, "Filtrar categoria").set_value("cat").run()
    filters = cast(IncidentFilters, fake.filter_calls[-1])
    assert filters.priority == "P2"
    assert filters.category == "cat"


def test_triage_and_document_state_do_not_cross_incidents() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Caso A", "", "", "", "", "", "", "", "cat-a")
    second = incident("I-2", "Caso B")
    second.category = "cat-b"
    fake.views.append(
        Model(
            incident=second,
            priority=None,
            category="cat-b",
            escalated=False,
        )
    )
    at = app(fake)
    at.sidebar.radio[0].set_value("Triagem").run()
    widget(at.button, "Executar triagem").click().run()
    assert any("triage_incomplete" in item.value for item in at.markdown)
    widget(at.selectbox, "Incidente").set_value("Caso B — I-2").run()
    assert not any("triage_incomplete" in item.value for item in at.markdown)
    assert any("Categoria persistida: cat-b" in item.value for item in at.caption)

    at.sidebar.radio[0].set_value("Procedimentos e documentos").run()
    widget(at.selectbox, "Incidente").set_value("Caso A — I-1").run()
    widget(at.text_input, "Ator gerador").set_value("analista")
    widget(at.button, "Gerar nova revisão").click().run()
    assert at.download_button
    widget(at.selectbox, "Incidente").set_value("Caso B — I-2").run()
    assert not at.download_button


@pytest.mark.parametrize(
    ("flow", "marker"),
    (
        ("create", "create_from_fields"),
        ("filters", "IncidentFilters("),
        ("detail", "get_incident"),
        ("update_all_fields", "update_from_fields"),
        ("close_reopen", "close_incident"),
        ("delete_confirmation", "if not confirmed:"),
        ("history", "incident_history"),
        ("triage_json", "run_triage_json"),
        ("knowledge", "enumerate(results, start=1)"),
        ("performed", "record_performed_fields"),
        ("documentation", "generate_documentation"),
        ("downloads", "st.download_button"),
        ("dashboard", "metrics.escalation_count"),
        ("triage_incident_binding", "bound[0] == incident_id"),
        ("document_incident_binding", "bound[0] == incident_id"),
    ),
)
def test_required_flow_is_wired_through_facade(flow: str, marker: str) -> None:
    source = Path("src/supportops/streamlit_app.py").read_text(encoding="utf-8")
    assert marker in source, flow
