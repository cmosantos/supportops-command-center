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


class InputValidationError(SupportOpsError):
    """Raised for invalid public input without echoing rejected values."""

    exit_code = 2


class NotFoundError(SupportOpsError):
    """Raised when an operationally visible record is absent."""

    exit_code = 4


class ConflictError(SupportOpsError):
    """Raised for optimistic concurrency conflicts."""

    exit_code = 5


class InvalidTransitionError(SupportOpsError):
    """Raised when an incident lifecycle transition is not allowed."""

    exit_code = 6


class PersistenceError(SupportOpsError):
    """Raised when persistence fails without exposing database details."""

    exit_code = 7


class KnowledgeError(SupportOpsError):
    """Raised when the local knowledge corpus cannot be used safely."""

    exit_code = 8
