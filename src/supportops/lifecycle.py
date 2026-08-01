"""Transactional incident lifecycle and approval services."""

import hashlib
import json
import sqlite3
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from uuid import uuid4

from supportops.domain.incidents import (
    ApprovalInput,
    HumanApproval,
    Incident,
    IncidentCreate,
    IncidentEvent,
    IncidentStatus,
    IncidentUpdate,
)
from supportops.errors import (
    ConflictError,
    InputValidationError,
    InvalidTransitionError,
    NotFoundError,
    PersistenceError,
)
from supportops.persistence.database import ConnectionFactory, UnitOfWork
from supportops.repositories import SQLiteApprovalRepository, SQLiteIncidentRepository

Clock = Callable[[], datetime]
IdGenerator = Callable[[], str]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


def canonical_snapshot(snapshot: Mapping[str, object]) -> str:
    return json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def snapshot_digest(snapshot: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_snapshot(snapshot).encode()).hexdigest()


class IncidentService:
    def __init__(
        self,
        factory: ConnectionFactory,
        clock: Clock = utc_now,
        id_generator: IdGenerator = new_id,
    ) -> None:
        self.factory = factory
        self.clock = clock
        self.id_generator = id_generator

    def create(self, data: IncidentCreate) -> Incident:
        now = self.clock()
        incident = Incident(
            id=self.id_generator(),
            **data.model_dump(exclude={"actor_reference"}),
            status=IncidentStatus.OPEN,
            version=1,
            created_at=now,
            updated_at=now,
            closed_at=None,
            deleted_at=None,
            deletion_reason=None,
            deletion_confirmed=False,
            pre_deletion_status=None,
            created_by=data.actor_reference,
        )
        try:
            with UnitOfWork(self.factory) as uow:
                repository = SQLiteIncidentRepository(uow.active_connection)
                repository.add(incident)
                repository.append_event(
                    self._event(incident, "INCIDENT_CREATED", None, IncidentStatus.OPEN)
                )
                uow.commit()
            return incident
        except sqlite3.Error:
            raise PersistenceError("Incident creation failed safely.") from None

    def get(self, incident_id: str) -> Incident:
        connection = self.factory.connect()
        try:
            incident = SQLiteIncidentRepository(connection).get(incident_id)
            if incident is None:
                raise NotFoundError("Incident was not found.")
            return incident
        finally:
            connection.close()

    def list(self) -> tuple[Incident, ...]:
        connection = self.factory.connect()
        try:
            return SQLiteIncidentRepository(connection).list()
        finally:
            connection.close()

    def update(
        self, incident_id: str, data: IncidentUpdate, actor: str | None = None
    ) -> Incident:
        changes = data.changes()
        if not changes:
            raise InputValidationError("At least one incident field must change.")
        now = self.clock()
        try:
            with UnitOfWork(self.factory) as uow:
                repository = SQLiteIncidentRepository(uow.active_connection)
                current = repository.get(incident_id)
                if current is None:
                    raise NotFoundError("Incident was not found.")
                if not repository.update_fields(
                    incident_id, data.expected_version, changes, now.isoformat()
                ):
                    raise ConflictError("Incident version conflict; reload and retry.")
                repository.append_event(
                    self._event(
                        current,
                        "INCIDENT_UPDATED",
                        current.status,
                        current.status,
                        actor,
                        {"fields": sorted(changes)},
                    )
                )
                uow.commit()
            return self.get(incident_id)
        except sqlite3.Error:
            raise PersistenceError("Incident update failed safely.") from None

    def close(self, incident_id: str, actor: str | None = None) -> Incident:
        return self._transition(
            incident_id, IncidentStatus.OPEN, IncidentStatus.CLOSED, actor
        )

    def reopen(self, incident_id: str, actor: str | None = None) -> Incident:
        return self._transition(
            incident_id, IncidentStatus.CLOSED, IncidentStatus.OPEN, actor
        )

    def soft_delete(
        self, incident_id: str, reason: str, confirmed: bool, actor: str | None = None
    ) -> None:
        normalized_reason = reason.strip()
        if not confirmed or not normalized_reason:
            raise InputValidationError(
                "Logical deletion requires confirmation and a reason."
            )
        now = self.clock()
        try:
            with UnitOfWork(self.factory) as uow:
                repository = SQLiteIncidentRepository(uow.active_connection)
                incident = repository.get(incident_id)
                if incident is None:
                    raise NotFoundError("Incident was not found.")
                if not repository.soft_delete(
                    incident, normalized_reason, now.isoformat()
                ):
                    raise ConflictError("Incident changed; reload and retry.")
                repository.append_event(
                    self._event(
                        incident,
                        "INCIDENT_SOFT_DELETED",
                        incident.status,
                        incident.status,
                        actor,
                        {"reason": normalized_reason},
                    )
                )
                uow.commit()
        except sqlite3.Error:
            raise PersistenceError("Incident deletion failed safely.") from None

    def history(
        self, incident_id: str, *, include_deleted: bool = False
    ) -> tuple[IncidentEvent, ...]:
        connection = self.factory.connect()
        try:
            repository = SQLiteIncidentRepository(connection)
            if repository.get(incident_id, include_deleted=include_deleted) is None:
                raise NotFoundError("Incident was not found.")
            return repository.history(incident_id)
        finally:
            connection.close()

    def record_approval(self, data: ApprovalInput) -> HumanApproval:
        if snapshot_digest(data.action_snapshot) != data.action_digest:
            raise InputValidationError("Action snapshot does not match its digest.")
        now = self.clock()
        approval = HumanApproval(
            id=self.id_generator(), **data.model_dump(), decided_at=now, created_at=now
        )
        try:
            with UnitOfWork(self.factory) as uow:
                incidents = SQLiteIncidentRepository(uow.active_connection)
                incident = incidents.get(data.incident_id)
                if incident is None:
                    raise NotFoundError("Incident was not found.")
                SQLiteApprovalRepository(uow.active_connection).add(approval)
                incidents.append_event(
                    self._event(
                        incident,
                        "APPROVAL_RECORDED",
                        incident.status,
                        incident.status,
                        data.approver_reference,
                        {
                            "approval_id": approval.id,
                            "action_id": data.action_id,
                            "action_version": data.action_version,
                            "decision": data.decision.value,
                        },
                    )
                )
                uow.commit()
            return approval
        except sqlite3.Error:
            raise PersistenceError("Approval recording failed safely.") from None

    def approval_matches(
        self, incident_id: str, action_id: str, action_version: int, action_digest: str
    ) -> bool:
        connection = self.factory.connect()
        try:
            return SQLiteApprovalRepository(connection).matches(
                incident_id, action_id, action_version, action_digest
            )
        finally:
            connection.close()

    def _transition(
        self,
        incident_id: str,
        expected: IncidentStatus,
        target: IncidentStatus,
        actor: str | None,
    ) -> Incident:
        now = self.clock()
        try:
            with UnitOfWork(self.factory) as uow:
                repository = SQLiteIncidentRepository(uow.active_connection)
                incident = repository.get(incident_id)
                if incident is None:
                    raise NotFoundError("Incident was not found.")
                if incident.status is not expected:
                    raise InvalidTransitionError(
                        f"Incident must be {expected.value} for this transition."
                    )
                if not repository.transition(
                    incident_id, expected.value, target.value, now.isoformat()
                ):
                    raise ConflictError("Incident changed; reload and retry.")
                repository.append_event(
                    self._event(
                        incident, f"INCIDENT_{target.value}", expected, target, actor
                    )
                )
                uow.commit()
            return self.get(incident_id)
        except sqlite3.Error:
            raise PersistenceError("Incident transition failed safely.") from None

    def _event(
        self,
        incident: Incident,
        event_type: str,
        previous: IncidentStatus | None,
        new: IncidentStatus | None,
        actor: str | None = None,
        details: dict[str, object] | None = None,
    ) -> IncidentEvent:
        return IncidentEvent(
            id=self.id_generator(),
            incident_id=incident.id,
            event_type=event_type,
            previous_status=previous,
            new_status=new,
            occurred_at=self.clock(),
            actor_reference=actor,
            details=details or {},
        )
