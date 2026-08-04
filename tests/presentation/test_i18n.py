"""English-only coverage for the Streamlit presentation layer."""

from datetime import UTC, datetime
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from supportops.i18n import catalog_keys, translate
from supportops.web_facade import DatabaseStatus


class DashboardFacade:
    """Small facade used to validate the English production interface."""

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


def production_entry(web: object, status: object) -> None:
    from supportops.streamlit_app import PRODUCTION_LANGUAGE, render_with_facade

    render_with_facade(web, status, language=PRODUCTION_LANGUAGE)


def test_english_catalog_contains_required_navigation_labels() -> None:
    keys = catalog_keys("en")
    assert {"area", "page_dashboard", "page_incidents", "page_triage"} <= keys
    assert translate("en", "page_incidents") == "Incidents"
    assert translate("en", "page_documents") == "Procedures and documents"


def test_production_dashboard_is_english_only() -> None:
    at = AppTest.from_function(
        production_entry,
        args=(DashboardFacade(), DatabaseStatus(4, (), 0)),
        default_timeout=10,
    ).run()

    assert not at.sidebar.selectbox
    assert at.metric[0].label == "Total incidents"
    assert at.sidebar.radio[0].label == "Area"
    assert "Incidents" in at.sidebar.radio[0].options
    assert any("pending migrations" in item.value for item in at.caption)


def test_english_navigation_preserves_current_page() -> None:
    at = AppTest.from_function(
        production_entry,
        args=(DashboardFacade(), DatabaseStatus(4, (), 0)),
        default_timeout=10,
    ).run()

    at.sidebar.radio[0].set_value("Incidents").run()

    assert at.sidebar.radio[0].value == "Incidents"
    assert any(header.value == "Incidents" for header in at.header)
    assert any(info.value == "No incidents found." for info in at.info)
    assert not at.metric

    at.run()

    assert at.sidebar.radio[0].value == "Incidents"
    assert any(header.value == "Incidents" for header in at.header)
