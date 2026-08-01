"""Composition root for offline application services."""

from dataclasses import dataclass

from supportops.config import Settings, get_settings
from supportops.contracts import DiagnosticsProvider, VersionProvider
from supportops.lifecycle import IncidentService
from supportops.persistence.database import ConnectionFactory, MigrationRunner
from supportops.services import InProcessDiagnosticsProvider, PackageVersionProvider


@dataclass(frozen=True, slots=True)
class Application:
    settings: Settings
    version_provider: VersionProvider
    diagnostics_provider: DiagnosticsProvider
    migration_runner: MigrationRunner
    incident_service: IncidentService


def build_application() -> Application:
    """Construct the local dependency graph without automatic database mutation."""

    settings = get_settings()
    factory = ConnectionFactory(settings.db_path, settings.db_busy_timeout_ms)
    return Application(
        settings=settings,
        version_provider=PackageVersionProvider(),
        diagnostics_provider=InProcessDiagnosticsProvider(),
        migration_runner=MigrationRunner(factory),
        incident_service=IncidentService(factory),
    )
