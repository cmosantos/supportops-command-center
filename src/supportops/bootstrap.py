"""Composition root for foundation services."""

from dataclasses import dataclass

from supportops.config import Settings, get_settings
from supportops.contracts import DiagnosticsProvider, VersionProvider
from supportops.services import InProcessDiagnosticsProvider, PackageVersionProvider


@dataclass(frozen=True, slots=True)
class Application:
    settings: Settings
    version_provider: VersionProvider
    diagnostics_provider: DiagnosticsProvider


def build_application() -> Application:
    """Construct the offline application dependency graph."""

    return Application(
        settings=get_settings(),
        version_provider=PackageVersionProvider(),
        diagnostics_provider=InProcessDiagnosticsProvider(),
    )
