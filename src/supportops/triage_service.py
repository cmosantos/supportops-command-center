"""Transactional application service for deterministic incident triage."""

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from supportops.domain.triage import TriageEvidence, TriageResult
from supportops.errors import NotFoundError, PersistenceError
from supportops.persistence.database import ConnectionFactory, UnitOfWork
from supportops.repositories import SQLiteIncidentRepository, SQLiteTriageRepository
from supportops.triage_engine import evaluate_triage
from supportops.triage_policy import TriagePolicy

Clock = Callable[[], datetime]
IdGenerator = Callable[[], str]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class TriageService:
    """Evaluate and atomically append one immutable snapshot per request."""

    def __init__(
        self,
        factory: ConnectionFactory,
        policy: TriagePolicy,
        clock: Clock = utc_now,
        id_generator: IdGenerator = new_id,
    ) -> None:
        self.factory = factory
        self.policy = policy
        self.clock = clock
        self.id_generator = id_generator

    def triage(
        self,
        incident_id: str,
        evidence: TriageEvidence,
        actor: str | None = None,
    ) -> TriageResult:
        try:
            with UnitOfWork(self.factory) as uow:
                incidents = SQLiteIncidentRepository(uow.active_connection)
                if incidents.get(incident_id) is None:
                    raise NotFoundError("Incident was not found.")
                evaluated = evaluate_triage(
                    self.policy,
                    evidence,
                    incident_id=incident_id,
                    snapshot_id=self.id_generator(),
                    generated_at=self.clock(),
                    created_by=actor,
                )
                stored = SQLiteTriageRepository(uow.active_connection).add(evaluated)
                uow.commit()
            return stored
        except sqlite3.Error:
            raise PersistenceError("Incident triage failed safely.") from None

    def history(self, incident_id: str) -> tuple[TriageResult, ...]:
        connection = self.factory.connect()
        try:
            if SQLiteIncidentRepository(connection).get(incident_id) is None:
                raise NotFoundError("Incident was not found.")
            return SQLiteTriageRepository(connection).list(incident_id)
        except sqlite3.Error:
            raise PersistenceError("Triage history retrieval failed safely.") from None
        finally:
            connection.close()

    def latest(self, incident_id: str) -> TriageResult | None:
        connection = self.factory.connect()
        try:
            if SQLiteIncidentRepository(connection).get(incident_id) is None:
                raise NotFoundError("Incident was not found.")
            return SQLiteTriageRepository(connection).latest(incident_id)
        except sqlite3.Error:
            raise PersistenceError("Triage retrieval failed safely.") from None
        finally:
            connection.close()
