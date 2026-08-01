from supportops.bootstrap import Application, build_application
from supportops.contracts import DiagnosticsProvider, VersionProvider


def test_composition_root_satisfies_foundation_contracts() -> None:
    application = build_application()

    assert isinstance(application, Application)
    assert isinstance(application.version_provider, VersionProvider)
    assert isinstance(application.diagnostics_provider, DiagnosticsProvider)
