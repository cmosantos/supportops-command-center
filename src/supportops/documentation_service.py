# ruff: noqa: E501
"""Persisted-only incident documentation application service."""

import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError

from supportops.contracts import IncidentExporter
from supportops.domain.documentation import (
    DocumentationSections,
    ExportFormat,
    IncidentDocumentation,
    PerformedProcedure,
    PerformedProcedureInput,
    WrittenExport,
)
from supportops.errors import InputValidationError, NotFoundError, PersistenceError
from supportops.exporters import ContainedExportWriter
from supportops.persistence.database import ConnectionFactory, UnitOfWork
from supportops.repositories import (
    SQLiteApprovalRepository,
    SQLiteDocumentationRepository,
    SQLiteIncidentRepository,
    SQLitePerformedProcedureRepository,
    SQLiteTriageRepository,
)

Clock = Callable[[], datetime]
IdGenerator = Callable[[], str]
NEUTRAL = "No persisted information available."


class DocumentationService:
    def __init__(
        self,
        factory: ConnectionFactory,
        writer: ContainedExportWriter,
        exporters: dict[ExportFormat, IncidentExporter],
        clock: Clock = lambda: datetime.now(UTC),
        id_generator: IdGenerator = lambda: str(uuid4()),
    ) -> None:
        self.factory = factory
        self.writer = writer
        self.exporters = exporters
        self.clock = clock
        self.id_generator = id_generator

    def record_performed(
        self, incident_id: str, data: PerformedProcedureInput
    ) -> PerformedProcedure:
        try:
            with UnitOfWork(self.factory) as uow:
                incidents = SQLiteIncidentRepository(uow.active_connection)
                if incidents.get(incident_id) is None:
                    raise NotFoundError("Incident was not found.")
                approvals = SQLiteApprovalRepository(uow.active_connection)
                if data.suggested_action_id and not approvals.action_exists(
                    incident_id,
                    data.suggested_action_id,
                    data.suggested_action_version or 0,
                    data.suggested_action_digest or "",
                ):
                    raise InputValidationError(
                        "Suggested action reference was not found for this incident."
                    )
                procedure = PerformedProcedure(
                    id=self.id_generator(),
                    incident_id=incident_id,
                    sequence=1,
                    description=data.description,
                    result=data.result,
                    performed_at=self.clock(),
                    actor_reference=data.actor_reference,
                    suggested_action_id=data.suggested_action_id,
                    suggested_action_version=data.suggested_action_version,
                    suggested_action_digest=data.suggested_action_digest,
                )
                stored = SQLitePerformedProcedureRepository(uow.active_connection).add(
                    procedure
                )
                uow.commit()
                return stored
        except sqlite3.Error:
            raise PersistenceError(
                "Performed procedure recording failed safely."
            ) from None
        except (ValidationError, ValueError, TypeError):
            raise PersistenceError(
                "Performed procedure recording failed safely."
            ) from None

    def list_performed(self, incident_id: str) -> tuple[PerformedProcedure, ...]:
        connection = self.factory.connect()
        try:
            if SQLiteIncidentRepository(connection).get(incident_id) is None:
                raise NotFoundError("Incident was not found.")
            try:
                return SQLitePerformedProcedureRepository(connection).list(incident_id)
            except (ValidationError, ValueError, TypeError):
                raise PersistenceError(
                    "Persisted performed procedure is invalid."
                ) from None
        finally:
            connection.close()

    def generate(self, incident_id: str, actor: str) -> IncidentDocumentation:
        actor = actor.strip()
        if not actor:
            raise InputValidationError("Documentation actor is required.")
        try:
            with UnitOfWork(self.factory) as uow:
                incidents = SQLiteIncidentRepository(uow.active_connection)
                incident = incidents.get(incident_id)
                if incident is None:
                    raise NotFoundError("Incident was not found.")
                events = incidents.history(incident_id)
                triage = SQLiteTriageRepository(uow.active_connection).list(incident_id)
                approvals = SQLiteApprovalRepository(uow.active_connection).list(
                    incident_id
                )
                performed = SQLitePerformedProcedureRepository(
                    uow.active_connection
                ).list(incident_id)
                suggested = tuple(
                    f"Suggestion {item.action_id} v{item.action_version} ({item.decision.value}): "
                    f"{json.dumps(item.action_snapshot, ensure_ascii=False, sort_keys=True)}"
                    for item in approvals
                ) or (NEUTRAL,)
                performed_lines = tuple(
                    f"{item.performed_at.isoformat()} — {item.description} — Result: {item.result} — Actor: {item.actor_reference}"
                    for item in performed
                ) or (NEUTRAL,)
                evidence = tuple(
                    [f"Symptoms: {incident.symptoms}"]
                    + [f"Error: {value}" for value in incident.error_messages]
                    + [
                        f"Triage revision {item.sequence}: {json.dumps(item.normalized_input, ensure_ascii=False, sort_keys=True)}"
                        for item in triage
                    ]
                    + [
                        f"Lifecycle event {item.sequence}: {item.event_type}"
                        for item in events
                    ]
                )
                last = performed[-1] if performed else None
                result_text = last.result if last else NEUTRAL
                sections = DocumentationSections(
                    executive_summary=f"Incident {incident.id}: {incident.title}. Status: {incident.status.value}.",
                    technical_description=f"{incident.description}\nAffected service: {incident.affected_service}. Affected party: {incident.affected_party}.",
                    collected_evidence=evidence or (NEUTRAL,),
                    evaluated_hypotheses=(NEUTRAL,),
                    suggested_procedures=suggested,
                    performed_procedures=performed_lines,
                    applied_solution=last.description if last else NEUTRAL,
                    result_and_preventive_recommendation=f"Result: {result_text}\nPreventive recommendation: {NEUTRAL}",
                    ticket_ready_text=f"{incident.title} — {incident.description} — Status: {incident.status.value} — Result: {result_text}",
                )
                draft = IncidentDocumentation(
                    id=self.id_generator(),
                    incident_id=incident_id,
                    revision=1,
                    generated_at=self.clock(),
                    generated_by=actor,
                    sections=sections,
                )
                stored = SQLiteDocumentationRepository(uow.active_connection).add(draft)
                uow.commit()
                return stored
        except sqlite3.Error:
            raise PersistenceError("Documentation generation failed safely.") from None
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError):
            raise PersistenceError("Persisted incident data is invalid.") from None

    def history(self, incident_id: str) -> tuple[IncidentDocumentation, ...]:
        connection = self.factory.connect()
        try:
            if SQLiteIncidentRepository(connection).get(incident_id) is None:
                raise NotFoundError("Incident was not found.")
            try:
                return SQLiteDocumentationRepository(connection).list(incident_id)
            except (json.JSONDecodeError, ValidationError, ValueError, TypeError):
                raise PersistenceError("Persisted documentation is invalid.") from None
        finally:
            connection.close()

    def get(
        self, incident_id: str, revision: int | None = None
    ) -> IncidentDocumentation:
        connection = self.factory.connect()
        try:
            if SQLiteIncidentRepository(connection).get(incident_id) is None:
                raise NotFoundError("Incident was not found.")
            repository = SQLiteDocumentationRepository(connection)
            document = (
                repository.latest(incident_id)
                if revision is None
                else repository.get(incident_id, revision)
            )
            if document is None:
                raise NotFoundError("Incident documentation was not found.")
            return document
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError):
            raise PersistenceError("Persisted documentation is invalid.") from None
        finally:
            connection.close()

    def export(
        self, incident_id: str, export_format: ExportFormat, revision: int | None = None
    ) -> WrittenExport:
        document = self.get(incident_id, revision)
        exporter = self.exporters.get(export_format)
        if exporter is None:
            raise InputValidationError("Unsupported export format.")
        return self.writer.write(exporter.export(document))
