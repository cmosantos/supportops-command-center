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


def incident(ident: str, title: str = "Case", status: str = "OPEN") -> Model:
    return Model(
        id=ident,
        title=title,
        description="Description",
        affected_party="Person",
        affected_service="Service",
        impact="low",
        urgency="low",
        symptoms="Symptom",
        category="category",
        status=Model(value=status),
        version=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        closed_at=None,
        created_by="actor",
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
                actor_reference="actor",
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
            questions=(Model(question="What is the impact?"),),
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
                matched_terms=("network",),
                excerpt="Evidence",
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
                name: "content"
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
    at.sidebar.radio[0].set_value("Incidents").run()
    widget(at.text_input, "Title").set_value("New")
    widget(at.text_input, "Affected party").set_value("Person")
    widget(at.text_input, "Affected service").set_value("Network")
    widget(at.text_area, "Description").set_value("Description")
    widget(at.text_area, "Symptoms").set_value("Symptom")
    widget(at.button, "Register").click().run()
    assert fake.calls.count("create") == 1
    at.run()
    assert fake.calls.count("create") == 1


def test_incident_filters_update_transitions_delete_and_history() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Case", "", "", "", "", "", "", "", "category")
    at = app(fake)
    at.sidebar.radio[0].set_value("Incidents").run()
    assert widget(at.selectbox, "Filter priority")
    assert widget(at.text_input, "Filter category")
    widget(at.text_input, "Filter text").set_value("missing").run()
    assert any(info.value == "No incidents found." for info in at.info)
    widget(at.text_input, "Filter text").set_value("").run()
    widget(at.text_input, "New title").set_value("Updated")
    widget(at.button, "Update").click().run()
    assert fake.update_args[2] == "Updated"
    assert fake.update_args[3:8] == (
        "Description",
        "Person",
        "Service",
        "Symptom",
        "category",
    )
    at.run()
    assert fake.calls.count("update") == 1
    widget(at.button, "Close").click().run()
    widget(at.button, "Reopen").click().run()
    assert {"update", "close", "reopen"}.issubset(fake.calls)
    at.run()
    assert fake.calls.count("close") == fake.calls.count("reopen") == 1
    widget(at.text_input, "Logical deletion reason").set_value("duplicate")
    widget(at.button, "Logically delete").click().run()
    assert "delete" not in fake.calls
    widget(at.checkbox, "I confirm the logical deletion of this incident").check()
    widget(at.button, "Logically delete").click().run()
    assert "delete" in fake.calls
    at.run()
    assert fake.calls.count("delete") == 1
    assert any("INCIDENT_CREATED" in str(value.value) for value in at.json)


def test_triage_and_knowledge_states_and_safe_errors() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Case", "", "", "", "", "", "", "", "cat")
    at = app(fake)
    at.sidebar.radio[0].set_value("Triage").run()
    widget(at.button, "Run triage").click().run()
    assert any("triage_incomplete" in item.value for item in at.markdown)
    widget(at.text_area, "Triage evidence (JSON)").set_value(
        '{"impact":"critical","urgency":"critical"}'
    )
    widget(at.button, "Run triage").click().run()
    assert any("Question:" in item.value for item in at.markdown)
    at.run()
    assert fake.calls.count("triage") == 2
    at.sidebar.radio[0].set_value("Knowledge").run()
    widget(at.text_input, "Query").set_value("network")
    widget(at.button, "Search").click().run()
    assert any("1. Runbook" in item.value for item in at.subheader)
    assert any(text.value == "Evidence" for text in at.text)
    widget(at.text_input, "Query").set_value("none")
    widget(at.button, "Search").click().run()
    assert any(info.value == "No matches found." for info in at.info)
    widget(at.text_input, "Query").set_value("error")
    widget(at.button, "Search").click().run()
    assert any(
        error.value == "The operation failed safely. Try again."
        for error in at.error
    )


def test_performed_document_nine_sections_and_two_downloads() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Case", "", "", "", "", "", "", "", "cat")
    at = app(fake)
    at.sidebar.radio[0].set_value("Procedures and documents").run()
    widget(at.text_area, "Procedure actually performed").set_value("Test")
    widget(at.text_area, "Observed result").set_value("OK")
    inputs = [item for item in at.text_input if item.label == "Responsible actor"]
    inputs[0].set_value("analyst")
    widget(at.button, "Record procedure").click().run()
    widget(at.text_input, "Generator actor").set_value("analyst")
    widget(at.button, "Generate new revision").click().run()
    assert fake.calls.count("performed") == fake.calls.count("document") == 1
    at.run()
    assert fake.calls.count("performed") == fake.calls.count("document") == 1
    assert len(at.download_button) == 2
    assert {item.label for item in at.download_button} == {
        "Download MARKDOWN",
        "Download JSON",
    }
    assert "executive_summary" in str(at.json[-1].value)


def test_priority_category_filters_are_passed_to_facade() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Case", "", "", "", "", "", "", "", "cat")
    at = app(fake)
    at.sidebar.radio[0].set_value("Incidents").run()
    widget(at.selectbox, "Filter priority").set_value("P2")
    widget(at.text_input, "Filter category").set_value("cat").run()
    filters = cast(IncidentFilters, fake.filter_calls[-1])
    assert filters.priority == "P2"
    assert filters.category == "cat"


def test_triage_and_document_state_do_not_cross_incidents() -> None:
    fake = FakeFacade()
    fake.create_from_fields("Case A", "", "", "", "", "", "", "", "cat-a")
    second = incident("I-2", "Case B")
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
    at.sidebar.radio[0].set_value("Triage").run()
    widget(at.button, "Run triage").click().run()
    assert any("triage_incomplete" in item.value for item in at.markdown)
    widget(at.selectbox, "Incident").set_value("Case B — I-2").run()
    assert not any("triage_incomplete" in item.value for item in at.markdown)
    assert any("Persisted category: cat-b" in item.value for item in at.caption)

    at.sidebar.radio[0].set_value("Procedures and documents").run()
    widget(at.selectbox, "Incident").set_value("Case A — I-1").run()
    widget(at.text_input, "Generator actor").set_value("analyst")
    widget(at.button, "Generate new revision").click().run()
    assert at.download_button
    widget(at.selectbox, "Incident").set_value("Case B — I-2").run()
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
