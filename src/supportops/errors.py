"""Safe application error types."""


class SupportOpsError(Exception):
    """Base error carrying text that is safe to display to an operator."""

    exit_code = 1

    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


class ConfigurationError(SupportOpsError):
    """Raised when local configuration cannot be validated."""

    exit_code = 2


class DiagnosticError(SupportOpsError):
    """Raised when an in-process diagnostic check fails unexpectedly."""

    exit_code = 3
