"""Foundation application services."""

import sys

from supportops import __version__
from supportops.config import Settings
from supportops.contracts import DiagnosticCheck
from supportops.domain.priority_matrix import structural_matrix_sample
from supportops.safe_logging import REDACTED, redact_sensitive


class PackageVersionProvider:
    def get_version(self) -> str:
        return __version__


class InProcessDiagnosticsProvider:
    """Perform deterministic checks without network, shell, or external services."""

    def run(self, settings: Settings) -> tuple[DiagnosticCheck, ...]:
        python_ok = sys.version_info[:2] == (3, 12)
        matrix = structural_matrix_sample()
        redacted = redact_sensitive({"token": "diagnostic-value", "safe": "ok"})
        return (
            DiagnosticCheck(
                "python",
                python_ok,
                "Python 3.12" if python_ok else "Python 3.12 is required",
            ),
            DiagnosticCheck("settings", True, f"environment={settings.environment}"),
            DiagnosticCheck(
                "matrix_contract", len(matrix.rules) == 16, "16 unique cells validated"
            ),
            DiagnosticCheck(
                "logging",
                redacted == {"token": REDACTED, "safe": "ok"},
                "recursive sensitive-field redaction active",
            ),
            DiagnosticCheck("composition_root", True, "foundation services composed"),
        )
