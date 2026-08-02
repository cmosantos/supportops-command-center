# ruff: noqa: E501
"""Repository ports and SQLite adapters for immutable lifecycle records."""

import json
import sqlite3
from datetime import datetime
from typing import Protocol

from supportops.domain.incidents import HumanApproval, Incident, IncidentEvent
from supportops.domain.triage import TriageOutcome, TriageResult

INCIDENT_COLUMNS = """id,title,description,affected_party,affected_service,impact,
urgency,symptoms,error_messages_json,actions_taken_json,status,version,created_at,
updated_at,closed_at,deleted_at,deletion_reason,deletion_confirmed,
pre_deletion_status,created_by"""
UPDATABLE_COLUMNS = frozenset(
    {"title", "description", "affected_party", "affected_service", "symptoms"}
)


class IncidentRepositoryPort(Protocol):
    def get(
        self, incident_id: str, *, include_deleted: bool = False
    ) -> Incident | None: ...
    def list(self) -> tuple[Incident, ...]: ...
    def history(self, incident_id: str) -> tuple[IncidentEvent, ...]: ...


class ApprovalRepositoryPort(Protocol):
    def add(self, approval: HumanApproval) -> None: ...
    def matches(
        self, incident_id: str, action_id: str, action_version: int, action_digest: str
    ) -> bool: ...


class TriageRepositoryPort(Protocol):
    def add(self, result: TriageResult) -> TriageResult: ...
    def list(self, incident_id: str) -> tuple[TriageResult, ...]: ...
    def latest(self, incident_id: str) -> TriageResult | None: ...


class SQLiteIncidentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, incident: Incident) -> None:
        self.connection.execute(
            f"INSERT INTO incidents({INCIDENT_COLUMNS}) VALUES ({','.join('?' for _ in range(20))})",  # noqa: S608
            self._incident_values(incident),
        )

    def get(
        self, incident_id: str, *, include_deleted: bool = False
    ) -> Incident | None:
        deletion_clause = "" if include_deleted else " AND deleted_at IS NULL"
        row = self.connection.execute(
            f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = ?{deletion_clause}",  # noqa: S608
            (incident_id,),
        ).fetchone()
        return self._to_incident(row) if row else None

    def list(self) -> tuple[Incident, ...]:
        found = self.connection.execute(
            f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE deleted_at IS NULL ORDER BY created_at, id"  # noqa: S608
        ).fetchall()
        return tuple(self._to_incident(row) for row in found)

    def update_fields(
        self, incident_id: str, expected_version: int, changes: dict[str, str], now: str
    ) -> bool:
        if not changes or not set(changes).issubset(UPDATABLE_COLUMNS):
            raise ValueError("update field is not allowlisted")
        assignments = ", ".join(f"{column} = ?" for column in sorted(changes))
        values: list[object] = [changes[column] for column in sorted(changes)]
        values.extend((now, incident_id, expected_version))
        cursor = self.connection.execute(
            f"UPDATE incidents SET {assignments}, updated_at = ?, version = version + 1 "  # noqa: S608
            "WHERE id = ? AND version = ? AND deleted_at IS NULL",
            tuple(values),
        )
        return cursor.rowcount == 1

    def transition(
        self,
        incident_id: str,
        expected_status: str,
        new_status: str,
        now: str,
    ) -> bool:
        closed_at: str | None = now if new_status == "CLOSED" else None
        cursor = self.connection.execute(
            "UPDATE incidents SET status = ?, closed_at = ?, updated_at = ?, version = version + 1 "
            "WHERE id = ? AND status = ? AND deleted_at IS NULL",
            (new_status, closed_at, now, incident_id, expected_status),
        )
        return cursor.rowcount == 1

    def soft_delete(self, incident: Incident, reason: str, now: str) -> bool:
        cursor = self.connection.execute(
            "UPDATE incidents SET deleted_at = ?, deletion_reason = ?, deletion_confirmed = 1, "
            "pre_deletion_status = ?, updated_at = ?, version = version + 1 "
            "WHERE id = ? AND version = ? AND deleted_at IS NULL",
            (now, reason, incident.status.value, now, incident.id, incident.version),
        )
        return cursor.rowcount == 1

    def append_event(self, event: IncidentEvent) -> None:
        next_sequence = self.connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 FROM incident_events "
            "WHERE incident_id = ?",
            (event.incident_id,),
        ).fetchone()[0]
        self.connection.execute(
            "INSERT INTO incident_events(id,incident_id,sequence,event_type,"
            "previous_status,new_status,occurred_at,actor_reference,details_json) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                event.id,
                event.incident_id,
                next_sequence,
                event.event_type,
                event.previous_status.value if event.previous_status else None,
                event.new_status.value if event.new_status else None,
                event.occurred_at.isoformat(),
                event.actor_reference,
                json.dumps(event.details, sort_keys=True, separators=(",", ":")),
            ),
        )

    def history(self, incident_id: str) -> tuple[IncidentEvent, ...]:
        found = self.connection.execute(
            "SELECT id,incident_id,sequence,event_type,previous_status,new_status,"
            "occurred_at,actor_reference,details_json FROM incident_events "
            "WHERE incident_id = ? ORDER BY sequence",
            (incident_id,),
        ).fetchall()
        return tuple(
            IncidentEvent(
                id=row["id"],
                incident_id=row["incident_id"],
                sequence=row["sequence"],
                event_type=row["event_type"],
                previous_status=row["previous_status"],
                new_status=row["new_status"],
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
                actor_reference=row["actor_reference"],
                details=json.loads(row["details_json"]),
            )
            for row in found
        )

    @staticmethod
    def _incident_values(incident: Incident) -> tuple[object, ...]:
        return (
            incident.id,
            incident.title,
            incident.description,
            incident.affected_party,
            incident.affected_service,
            incident.impact.value,
            incident.urgency.value,
            incident.symptoms,
            json.dumps(incident.error_messages),
            json.dumps(incident.actions_already_taken),
            incident.status.value,
            incident.version,
            incident.created_at.isoformat(),
            incident.updated_at.isoformat(),
            incident.closed_at.isoformat() if incident.closed_at else None,
            incident.deleted_at.isoformat() if incident.deleted_at else None,
            incident.deletion_reason,
            int(incident.deletion_confirmed),
            incident.pre_deletion_status.value
            if incident.pre_deletion_status
            else None,
            incident.created_by,
        )

    @staticmethod
    def _to_incident(row: sqlite3.Row) -> Incident:
        return Incident(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            affected_party=row["affected_party"],
            affected_service=row["affected_service"],
            impact=row["impact"],
            urgency=row["urgency"],
            symptoms=row["symptoms"],
            error_messages=tuple(json.loads(row["error_messages_json"])),
            actions_already_taken=tuple(json.loads(row["actions_taken_json"])),
            status=row["status"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            closed_at=datetime.fromisoformat(row["closed_at"])
            if row["closed_at"]
            else None,
            deleted_at=datetime.fromisoformat(row["deleted_at"])
            if row["deleted_at"]
            else None,
            deletion_reason=row["deletion_reason"],
            deletion_confirmed=bool(row["deletion_confirmed"]),
            pre_deletion_status=row["pre_deletion_status"],
            created_by=row["created_by"],
        )


class SQLiteApprovalRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, approval: HumanApproval) -> None:
        self.connection.execute(
            "INSERT INTO human_approvals(id,incident_id,action_id,action_version,action_digest,"
            "action_snapshot_json,decision,approver_reference,decided_at,note,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                approval.id,
                approval.incident_id,
                approval.action_id,
                approval.action_version,
                approval.action_digest,
                json.dumps(
                    approval.action_snapshot, sort_keys=True, separators=(",", ":")
                ),
                approval.decision.value,
                approval.approver_reference,
                approval.decided_at.isoformat(),
                approval.note,
                approval.created_at.isoformat(),
            ),
        )

    def matches(
        self, incident_id: str, action_id: str, action_version: int, action_digest: str
    ) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM human_approvals WHERE incident_id = ? AND action_id = ? "
            "AND action_version = ? AND action_digest = ? AND decision = 'APPROVED' LIMIT 1",
            (incident_id, action_id, action_version, action_digest),
        ).fetchone()
        return row is not None


class SQLiteTriageRepository:
    """Append-only adapter for immutable triage snapshots and questions."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, result: TriageResult) -> TriageResult:
        sequence = self.connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 FROM triage_snapshots "
            "WHERE incident_id = ?",
            (result.incident_id,),
        ).fetchone()[0]
        stored = result.model_copy(update={"sequence": sequence})
        input_snapshot = stored.normalized_input
        self.connection.execute(
            "INSERT INTO triage_snapshots("
            "id,incident_id,sequence,policy_id,schema_version,matrix_version,"
            "policy_checksum,input_snapshot_json,result_snapshot_json,outcome,"
            "priority,recommended_route,escalation_required,missing_evidence_json,"
            "questions_json,risk_signal_ids_json,stop_reason_ids_json,"
            "escalation_reason_ids_json,created_at,created_by) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                stored.snapshot_id,
                stored.incident_id,
                sequence,
                stored.policy_id,
                stored.schema_version,
                stored.matrix_version,
                stored.policy_checksum,
                self._json(input_snapshot),
                stored.model_dump_json(),
                "COMPLETE"
                if stored.outcome is TriageOutcome.COMPLETE
                else "INCOMPLETE",
                stored.priority.value if stored.priority else None,
                stored.recommended_route.value if stored.recommended_route else None,
                int(stored.escalation_required),
                self._json(stored.missing_evidence),
                self._json(
                    [question.model_dump(mode="json") for question in stored.questions]
                ),
                self._json(input_snapshot.get("risk_signal_ids", [])),
                self._json(stored.stop.reason_ids),
                self._json(stored.escalation_reason_ids),
                stored.generated_at.isoformat(),
                stored.created_by,
            ),
        )
        return stored

    def list(self, incident_id: str) -> tuple[TriageResult, ...]:
        found = self.connection.execute(
            "SELECT result_snapshot_json FROM triage_snapshots "
            "WHERE incident_id = ? ORDER BY sequence",
            (incident_id,),
        ).fetchall()
        return tuple(
            TriageResult.model_validate_json(row["result_snapshot_json"])
            for row in found
        )

    def latest(self, incident_id: str) -> TriageResult | None:
        row = self.connection.execute(
            "SELECT result_snapshot_json FROM triage_snapshots "
            "WHERE incident_id = ? ORDER BY sequence DESC LIMIT 1",
            (incident_id,),
        ).fetchone()
        return (
            TriageResult.model_validate_json(row["result_snapshot_json"])
            if row
            else None
        )

    @staticmethod
    def _json(value: object) -> str:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
