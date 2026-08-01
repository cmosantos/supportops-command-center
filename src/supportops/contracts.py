"""Small structural contracts used by the composition root."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from supportops.config import Settings


@runtime_checkable
class VersionProvider(Protocol):
    def get_version(self) -> str:
        """Return the canonical application version."""


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    name: str
    passed: bool
    detail: str


@runtime_checkable
class DiagnosticsProvider(Protocol):
    def run(self, settings: Settings) -> tuple[DiagnosticCheck, ...]:
        """Run in-process diagnostics only."""
