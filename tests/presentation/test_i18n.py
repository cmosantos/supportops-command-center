"""Localization coverage for the Streamlit presentation layer."""

from datetime import UTC, datetime
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from supportops.i18n import catalog_keys, translate
from supportops.web_facade import DatabaseStatus


class DashboardFacade:
    """Small facade used to validate both interface languages."""

    def dashboard(self) -> SimpleNamespace:
        return SimpleNamespace(
            total_incidents=0,
            by_priority=(),
            by_category=(),
            open_count=0,
            closed_count=0,
            mean_handling_seconds=None,
            escalation_count=0,
            calculated_at=datetime.now(UTC),
        )

    def parse_status(self, value: str) -> None:
        return None

    def list_incidents(self, filters: object = None) -> tuple[object, ...]:
        return ()


def injected_entry(web: object, status: object) -> None:
    from supportops.streamlit_app import render_with_facade

    render_with_facade(web, status)


def test_portuguese_and_english_catalogs_have_identical_keys() -> None:
    assert catalog_keys("pt-BR") == catalog_keys("en")
    assert translate("pt-BR", "page_incidents") == "Incidentes"
    assert translate("en", "page_incidents") == "Incidents"


def test_dashboard_switches_from_portuguese_to_english() -> None:
    at = AppTest.from_function(
        injected_entry,
        args=(DashboardFacade(), DatabaseStatus(4, (), 0)),
        default_timeout=10,
    ).run()

    assert at.sidebar.selectbox[0].value == "Português"
    assert at.metric[0].label == "Total de incidentes"
    assert at.sidebar.radio[0].label == "Área"

    at.sidebar.selectbox[0].set_value("English").run()

    assert at.metric[0].label == "Total incidents"
    assert at.sidebar.radio[0].label == "Area"
    assert "Incidents" in at.sidebar.radio[0].options
    assert any("pending migrations" in item.value for item in at.caption)


def test_language_switch_preserves_current_page() -> None:
    at = AppTest.from_function(
        injected_entry,
        args=(DashboardFacade(), DatabaseStatus(4, (), 0)),
        default_timeout=10,
    ).run()

    at.sidebar.radio[0].set_value("Incidentes").run()
    assert any(header.value == "Incidentes" for header in at.header)
    assert any(info.value == "Nenhum incidente encontrado." for info in at.info)

    at.sidebar.selectbox[0].set_value("English").run()

    assert at.sidebar.radio[0].value == "Incidents"
    assert any(header.value == "Incidents" for header in at.header)
    assert any(info.value == "No incidents found." for info in at.info)
    assert not at.metric
