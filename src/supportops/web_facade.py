"""Typed application facade for presentation adapters."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import ValidationError

from supportops.documentation_service import DocumentationService
from supportops.domain.documentation import (
    ExportArtifact,
    ExportFormat,
    IncidentDocumentation,
    PerformedProcedure,
    PerformedProcedureInput,
)
from supportops.domain.incidents import (
    Incident,
    IncidentCreate,
    IncidentEvent,
    IncidentStatus,
    IncidentUpdate,
)
from supportops.domain.knowledge import SearchResult
from supportops.domain.priority_matrix import Impact, Urgency
from supportops.domain.triage import TriageEvidence, TriageResult
from supportops.errors import InputValidationError
from supportops.knowledge_service import KnowledgeService
from supportops.lifecycle import IncidentService
from supportops.persistence.database import MigrationRunner
from supportops.triage_service import TriageService


@dataclass(frozen=True, slots=True)
class DatabaseStatus:
    current_version: int
    pending_versions: tuple[int, ...]
    applied_count: int


@dataclass(frozen=True, slots=True)
class IncidentFilters:
    status: IncidentStatus | None = None
    priority: str | None = None
    category: str | None = None
    text: str | None = None


@dataclass(frozen=True, slots=True)
class IncidentView:
    incident: Incident
    priority: str | None
    category: str | None
    escalated: bool


@dataclass(frozen=True, slots=True)
class DashboardMetrics:
    total_incidents: int
    by_priority: tuple[tuple[str, int], ...]
    by_category: tuple[tuple[str, int], ...]
    open_count: int
    closed_count: int
    mean_handling_seconds: float | None
    escalation_count: int
    calculated_at: datetime


class SupportOpsFacade:
    """Application-owned orchestration and observational queries for web clients."""

    def __init__(
        self,
        migrations: MigrationRunner,
        incidents: IncidentService,
        triage: TriageService,
        knowledge: KnowledgeService,
        documentation: DocumentationService,
    ) -> None:
        self._migrations = migrations
        self._incidents = incidents
        self._triage = triage
        self._knowledge = knowledge
        self._documentation = documentation

    def bootstrap_database(self) -> DatabaseStatus:
        applied = self._migrations.apply(datetime.now(UTC).isoformat())
        current, pending = self._migrations.status()
        return DatabaseStatus(current, pending, applied)

    def list_incidents(
        self, filters: IncidentFilters | None = None
    ) -> tuple[IncidentView, ...]:
        filters = filters or IncidentFilters()
        views = tuple(self._view(item) for item in self._incidents.list())
        needle = (filters.text or "").strip().casefold()
        return tuple(
            view
            for view in views
            if (filters.status is None or view.incident.status is filters.status)
            and (filters.priority is None or view.priority == filters.priority)
            and (filters.category is None or view.category == filters.category)
            and (
                not needle
                or needle in view.incident.title.casefold()
                or needle in view.incident.description.casefold()
                or needle in view.incident.affected_service.casefold()
            )
        )

    def get_incident(self, incident_id: str) -> IncidentView:
        return self._view(self._incidents.get(incident_id))

    def create_incident(self, data: IncidentCreate) -> IncidentView:
        return self._view(self._incidents.create(data))

    @staticmethod
    def parse_status(value: str) -> IncidentStatus | None:
        return None if value == "Todos" else IncidentStatus(value)

    def create_from_fields(
        self,
        title: str,
        description: str,
        party: str,
        service: str,
        impact: str,
        urgency: str,
        symptoms: str,
        actor: str,
        category: str = "",
    ) -> IncidentView:
        return self.create_incident(
            IncidentCreate(
                title=title,
                description=description,
                affected_party=party,
                affected_service=service,
                category=category or None,
                impact=Impact(impact),
                urgency=Urgency(urgency),
                symptoms=symptoms,
                actor_reference=actor or None,
            )
        )

    def update_from_fields(
        self,
        incident_id: str,
        version: int,
        title: str,
        description: str,
        party: str,
        service: str,
        symptoms: str,
        category: str,
        actor: str,
    ) -> IncidentView:
        return self.update_incident(
            incident_id,
            IncidentUpdate(
                expected_version=version,
                title=title,
                description=description,
                affected_party=party,
                affected_service=service,
                symptoms=symptoms,
                category=category or None,
            ),
            actor or None,
        )

    def update_incident(
        self, incident_id: str, data: IncidentUpdate, actor: str | None
    ) -> IncidentView:
        return self._view(self._incidents.update(incident_id, data, actor))

    def close_incident(self, incident_id: str, actor: str | None) -> IncidentView:
        return self._view(self._incidents.close(incident_id, actor))

    def reopen_incident(self, incident_id: str, actor: str | None) -> IncidentView:
        return self._view(self._incidents.reopen(incident_id, actor))

    def delete_incident(
        self, incident_id: str, reason: str, confirmed: bool, actor: str | None
    ) -> None:
        self._incidents.soft_delete(incident_id, reason, confirmed, actor)

    def incident_history(self, incident_id: str) -> tuple[IncidentEvent, ...]:
        return self._incidents.history(incident_id)

    def run_triage(
        self, incident_id: str, evidence: TriageEvidence, actor: str | None
    ) -> TriageResult:
        return self._triage.triage(incident_id, evidence, actor)

    def run_basic_triage(
        self, incident_id: str, impact: str, urgency: str, actor: str
    ) -> TriageResult:
        return self.run_triage(
            incident_id,
            TriageEvidence(
                impact=Impact(impact) if impact else None,
                urgency=Urgency(urgency) if urgency else None,
            ),
            actor or None,
        )

    def run_triage_json(
        self, incident_id: str, evidence_json: str, actor: str
    ) -> TriageResult:
        try:
            raw = json.loads(evidence_json)
            if not isinstance(raw, dict):
                raise ValueError
            evidence = TriageEvidence.model_validate(raw)
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError):
            raise InputValidationError(
                "Triage evidence must be a valid JSON object."
            ) from None
        return self.run_triage(incident_id, evidence, actor or None)

    def triage_history(self, incident_id: str) -> tuple[TriageResult, ...]:
        return self._triage.history(incident_id)

    def search_knowledge(self, query: str, limit: int = 10) -> tuple[SearchResult, ...]:
        return self._knowledge.search(query, limit)

    def record_performed(
        self, incident_id: str, data: PerformedProcedureInput
    ) -> PerformedProcedure:
        return self._documentation.record_performed(incident_id, data)

    def record_performed_fields(
        self, incident_id: str, description: str, result: str, actor: str
    ) -> PerformedProcedure:
        return self.record_performed(
            incident_id,
            PerformedProcedureInput(
                description=description, result=result, actor_reference=actor
            ),
        )

    def performed_history(self, incident_id: str) -> tuple[PerformedProcedure, ...]:
        return self._documentation.list_performed(incident_id)

    def generate_documentation(
        self, incident_id: str, actor: str
    ) -> IncidentDocumentation:
        return self._documentation.generate(incident_id, actor)

    def documentation_history(
        self, incident_id: str
    ) -> tuple[IncidentDocumentation, ...]:
        return self._documentation.history(incident_id)

    def get_documentation(
        self, incident_id: str, revision: int | None = None
    ) -> IncidentDocumentation:
        return self._documentation.get(incident_id, revision)

    def export_content(
        self, incident_id: str, export_format: ExportFormat, revision: int | None = None
    ) -> ExportArtifact:
        return self._documentation.export_content(incident_id, export_format, revision)

    def export_content_name(
        self, incident_id: str, export_format: str, revision: int | None = None
    ) -> ExportArtifact:
        return self.export_content(incident_id, ExportFormat(export_format), revision)

    def dashboard(self) -> DashboardMetrics:
        incidents = self._incidents.list()
        views = tuple(self._view(item) for item in incidents)
        priorities: dict[str, int] = {}
        categories: dict[str, int] = {}
        escalations = 0
        for view in views:
            if view.priority:
                priorities[view.priority] = priorities.get(view.priority, 0) + 1
            if view.category:
                categories[view.category] = categories.get(view.category, 0) + 1
            escalations += int(view.escalated)
        durations = [
            item.handling_seconds
            for item in incidents
            if item.status is IncidentStatus.CLOSED
            and item.handling_seconds is not None
        ]
        return DashboardMetrics(
            len(incidents),
            tuple(sorted(priorities.items())),
            tuple(sorted(categories.items())),
            sum(item.status is IncidentStatus.OPEN for item in incidents),
            sum(item.status is IncidentStatus.CLOSED for item in incidents),
            sum(durations) / len(durations) if durations else None,
            escalations,
            datetime.now(UTC),
        )

    def _view(self, incident: Incident) -> IncidentView:
        latest = self._triage.latest(incident.id)
        return IncidentView(
            incident,
            latest.priority.value if latest and latest.priority else None,
            incident.category,
            bool(latest and latest.escalation_required),
        )
