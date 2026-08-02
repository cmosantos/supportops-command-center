from dataclasses import replace

import pytest

from supportops.bootstrap import build_application
from supportops.cli import GENERIC_ERROR, build_parser, dispatch, main
from supportops.contracts import DiagnosticCheck
from supportops.errors import ConfigurationError


def test_version_uses_composed_version_provider(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = main(["version"])

    assert result == 0
    assert capsys.readouterr().out.strip() == "1.0.0"


def test_config_validate_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["config", "validate"]) == 0
    assert capsys.readouterr().out.strip() == "Configuration is valid."


def test_configuration_failure_is_safe(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_build() -> None:
        raise ConfigurationError("Invalid configuration. See .env.example.")

    monkeypatch.setattr("supportops.cli.build_application", fail_build)

    assert main(["config", "validate"]) == 2
    output = capsys.readouterr().out
    assert "Invalid configuration" in output
    assert "Traceback" not in output


def test_unexpected_failure_is_generic(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    sensitive_detail = "private-value"

    def fail_build() -> None:
        raise RuntimeError(sensitive_detail)

    monkeypatch.setattr("supportops.cli.build_application", fail_build)

    assert main(["doctor"]) == 1
    output = capsys.readouterr().out
    assert GENERIC_ERROR in output
    assert sensitive_detail not in output
    assert "Traceback" not in output


def test_doctor_nonzero_when_a_check_fails(
    capsys: pytest.CaptureFixture[str],
) -> None:
    application = build_application()

    class FailedDiagnostics:
        def run(self, settings: object) -> tuple[DiagnosticCheck, ...]:
            return (DiagnosticCheck("python", False, "Python 3.12 is required"),)

    failed_application = replace(application, diagnostics_provider=FailedDiagnostics())

    assert dispatch(build_parser().parse_args(["doctor"]), failed_application) == 1
    assert "[FAIL] python" in capsys.readouterr().out
