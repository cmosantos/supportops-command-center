# ruff: noqa: E501
"""Real-SQLite tests for the application web facade and dashboard."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from supportops.documentation_service import DocumentationService
from supportops.domain.documentation import ExportFormat
from supportops.domain.triage import TriageEvidence
from supportops.exporters import (
    ContainedExportWriter,
    JsonIncidentExporter,
    MarkdownIncidentExporter,
)
from supportops.knowledge_search import MarkdownKnowledgeSearch
from supportops.knowledge_service import KnowledgeService
from supportops.lifecycle import IncidentService
from supportops.persistence.database import ConnectionFactory, MigrationRunner
from supportops.triage_policy import load_triage_policy
from supportops.triage_service import TriageService
from supportops.web_facade import IncidentFilters, SupportOpsFacade


def _facade(tmp_path: Path) -> SupportOpsFacade:
    factory = ConnectionFactory(tmp_path / "db.sqlite", 1000)
    migrations = MigrationRunner(factory)
    incidents = IncidentService(factory)
    triage = TriageService(factory, load_triage_policy(None))
    knowledge = KnowledgeService(
        MarkdownKnowledgeSearch(Path(__file__).parents[2] / "src/supportops/knowledge")
    )
    documentation = DocumentationService(
        factory,
        ContainedExportWriter(tmp_path / "exports"),
        {
            ExportFormat.MARKDOWN: MarkdownIncidentExporter(),
            ExportFormat.JSON: JsonIncidentExporter(),
        },
    )
    return SupportOpsFacade(migrations, incidents, triage, knowledge, documentation)


def test_dashboard_empty_and_lifecycle_metrics(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    assert facade.bootstrap_database().current_version == 4
    empty = facade.dashboard()
    assert empty.total_incidents == empty.open_count == empty.closed_count == 0
    assert empty.mean_handling_seconds is None

    first = facade.create_from_fields(
        "Rede indisponível",
        "Sem conectividade",
        "Usuário A",
        "Rede",
        "high",
        "high",
        "Sem acesso",
        "analista",
        "network",
    )
    second = facade.create_from_fields(
        "OneDrive",
        "Sem sincronização",
        "Usuário B",
        "OneDrive",
        "moderate",
        "moderate",
        "Fila parada",
        "analista",
        "storage",
    )
    facade.close_incident(first.incident.id, "analista")
    metrics = facade.dashboard()
    assert (metrics.total_incidents, metrics.open_count, metrics.closed_count) == (
        2,
        1,
        1,
    )
    assert metrics.mean_handling_seconds is not None
    assert metrics.by_category == (("network", 1), ("storage", 1))
    facade.delete_incident(second.incident.id, "duplicado", True, "analista")
    assert facade.dashboard().total_incidents == 1


def test_filters_and_safe_export_content(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    facade.bootstrap_database()
    incident = facade.create_from_fields(
        "Caixa compartilhada",
        "Acesso negado",
        "Equipe",
        "Outlook",
        "low",
        "low",
        "Erro de permissão",
        "analista",
        "messaging",
    )
    assert (
        facade.list_incidents(IncidentFilters(text="OUTLOOK"))[0].incident.id
        == incident.incident.id
    )
    assert facade.list_incidents(IncidentFilters(text="inexistente")) == ()
    assert len(facade.list_incidents(IncidentFilters(category="messaging"))) == 1
    facade.record_performed_fields(
        incident.incident.id, "Validou associação", "Confirmada", "analista"
    )
    document = facade.generate_documentation(incident.incident.id, "analista")
    artifact = facade.export_content_name(
        incident.incident.id, "json", document.revision
    )
    assert artifact.filename.endswith(".json")
    assert artifact.content.startswith(b"{")
    assert not (tmp_path / "exports" / artifact.filename).exists()


def complete_evidence(
    impact: str, urgency: str, *, escalated: bool = False
) -> TriageEvidence:
    return TriageEvidence.model_validate(
        {
            "impact": impact,
            "urgency": urgency,
            "supported_impact_criteria": [impact],
            "supported_urgency_criteria": [urgency],
            "affected_scope": "department",
            "scope_source": "service desk",
            "affected_process": "operations",
            "process_criticality": "validated",
            "workaround_status": "limited",
            "workaround_validation": "tested",
            "business_consequence": "delay",
            "containment_status": "stable",
            "critical_impact_reassessment": "not critical",
            "deadline": "today",
            "deadline_owner": "owner",
            "delay_consequence": "missed cutoff",
            "time_to_harm": "hours",
            "condition_stability": "stable",
            "failure_frequency": "continuous",
            "trend": "stable",
            "symptom_context": "observed",
            "prior_actions": "read-only checks",
            "recent_change": "none",
            "corroboration": "tickets",
            "risk_assessment_status": "none_identified",
            "requires_admin_or_change": False,
            "within_approved_runbook_or_noninvasive": True,
            "n1_safe_boundary": True,
            "expected_result_defined": True,
            "stop_condition_defined": True,
            "cross_team_or_vendor": escalated,
        }
    )


def test_dashboard_real_sqlite_mixed_latest_close_and_deleted(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    facade.bootstrap_database()
    now = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    facade._incidents.clock = lambda: now
    facade._triage.clock = lambda: now
    high = facade.create_from_fields(
        "High", "D", "A", "S", "high", "high", "X", "actor", "zeta"
    )
    low = facade.create_from_fields(
        "Low", "D", "B", "S", "low", "low", "X", "actor", "alpha"
    )
    facade.run_triage(
        high.incident.id, complete_evidence("high", "high", escalated=True), "actor"
    )
    facade.run_triage(low.incident.id, complete_evidence("low", "low"), "actor")
    now += timedelta(seconds=10)
    facade.close_incident(high.incident.id, "actor")
    now += timedelta(seconds=10)
    facade.reopen_incident(high.incident.id, "actor")
    now += timedelta(seconds=30)
    facade.close_incident(high.incident.id, "actor")
    metrics = facade.dashboard()
    assert metrics.by_priority == (("P2", 1), ("P4", 1))
    assert metrics.by_category == (("alpha", 1), ("zeta", 1))
    assert (metrics.open_count, metrics.closed_count, metrics.escalation_count) == (
        1,
        1,
        1,
    )
    assert metrics.mean_handling_seconds == 50.0
    assert facade.dashboard().by_priority == metrics.by_priority
    facade.delete_incident(low.incident.id, "duplicate", True, "actor")
    after = facade.dashboard()
    assert after.total_incidents == 1
    assert after.by_priority == (("P2", 1),)
    assert after.by_category == (("zeta", 1),)
    assert (after.open_count, after.closed_count, after.escalation_count) == (0, 1, 1)
