"""Composition root for offline application services."""

from dataclasses import dataclass
from pathlib import Path

from supportops.config import Settings, get_settings
from supportops.contracts import DiagnosticsProvider, VersionProvider
from supportops.documentation_service import DocumentationService
from supportops.domain.documentation import ExportFormat
from supportops.exporters import (
    ContainedExportWriter,
    JsonIncidentExporter,
    MarkdownIncidentExporter,
)
from supportops.knowledge_search import MarkdownKnowledgeSearch
from supportops.knowledge_service import KnowledgeService
from supportops.lifecycle import IncidentService
from supportops.persistence.database import ConnectionFactory, MigrationRunner
from supportops.services import InProcessDiagnosticsProvider, PackageVersionProvider
from supportops.triage_policy import load_triage_policy
from supportops.triage_service import TriageService
from supportops.web_facade import SupportOpsFacade


@dataclass(frozen=True, slots=True)
class Application:
    settings: Settings
    version_provider: VersionProvider
    diagnostics_provider: DiagnosticsProvider
    migration_runner: MigrationRunner
    incident_service: IncidentService
    triage_service: TriageService
    knowledge_service: KnowledgeService
    documentation_service: DocumentationService
    web: SupportOpsFacade


def build_application() -> Application:
    """Construct the local dependency graph without automatic database mutation."""

    settings = get_settings()
    factory = ConnectionFactory(settings.db_path, settings.db_busy_timeout_ms)
    migration_runner = MigrationRunner(factory)
    policy = load_triage_policy(settings.triage_policy_path)
    knowledge_root = Path(__file__).with_name("knowledge")
    incident_service = IncidentService(factory)
    triage_service = TriageService(factory, policy)
    knowledge_service = KnowledgeService(MarkdownKnowledgeSearch(knowledge_root))
    documentation_service = DocumentationService(
        factory,
        ContainedExportWriter(settings.export_root),
        {
            ExportFormat.MARKDOWN: MarkdownIncidentExporter(),
            ExportFormat.JSON: JsonIncidentExporter(),
        },
    )
    return Application(
        settings=settings,
        version_provider=PackageVersionProvider(),
        diagnostics_provider=InProcessDiagnosticsProvider(),
        migration_runner=migration_runner,
        incident_service=incident_service,
        triage_service=triage_service,
        knowledge_service=knowledge_service,
        documentation_service=documentation_service,
        web=SupportOpsFacade(
            migration_runner,
            incident_service,
            triage_service,
            knowledge_service,
            documentation_service,
        ),
    )
