# ruff: noqa: E501
"""Ordered, checksummed SQLite migrations."""

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    description: str
    statements: tuple[str, ...]

    @property
    def checksum(self) -> str:
        payload = "\n".join(self.statements).encode()
        return hashlib.sha256(payload).hexdigest()


MIGRATIONS = (
    Migration(
        1,
        "incident lifecycle and immutable audit records",
        (
            """CREATE TABLE incidents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                affected_party TEXT NOT NULL,
                affected_service TEXT NOT NULL,
                impact TEXT NOT NULL CHECK (impact IN ('low','moderate','high','critical')),
                urgency TEXT NOT NULL CHECK (urgency IN ('low','moderate','high','critical')),
                symptoms TEXT NOT NULL,
                error_messages_json TEXT NOT NULL,
                actions_taken_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('OPEN','CLOSED')),
                version INTEGER NOT NULL CHECK (version >= 1),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                closed_at TEXT,
                deleted_at TEXT,
                deletion_reason TEXT,
                deletion_confirmed INTEGER NOT NULL DEFAULT 0 CHECK (deletion_confirmed IN (0,1)),
                pre_deletion_status TEXT CHECK (pre_deletion_status IN ('OPEN','CLOSED')),
                created_by TEXT,
                CHECK ((deleted_at IS NULL AND deletion_reason IS NULL AND deletion_confirmed = 0 AND pre_deletion_status IS NULL)
                    OR (deleted_at IS NOT NULL AND length(trim(deletion_reason)) > 0 AND deletion_confirmed = 1 AND pre_deletion_status IS NOT NULL))
            )""",
            """CREATE TABLE incident_events (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE RESTRICT,
                sequence INTEGER NOT NULL CHECK (sequence > 0),
                event_type TEXT NOT NULL,
                previous_status TEXT CHECK (previous_status IN ('OPEN','CLOSED')),
                new_status TEXT CHECK (new_status IN ('OPEN','CLOSED')),
                occurred_at TEXT NOT NULL,
                actor_reference TEXT,
                details_json TEXT NOT NULL,
                UNIQUE (incident_id, sequence)
            )""",
            """CREATE TABLE human_approvals (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE RESTRICT,
                action_id TEXT NOT NULL,
                action_version INTEGER NOT NULL CHECK (action_version >= 1),
                action_digest TEXT NOT NULL CHECK (length(action_digest) = 64),
                action_snapshot_json TEXT NOT NULL,
                decision TEXT NOT NULL CHECK (decision IN ('PENDING','APPROVED','REJECTED')),
                approver_reference TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )""",
            "CREATE INDEX ix_incidents_created_at ON incidents(created_at)",
            "CREATE INDEX ix_incidents_status_deleted ON incidents(status, deleted_at)",
            "CREATE INDEX ix_events_incident_sequence ON incident_events(incident_id, sequence)",
            "CREATE INDEX ix_approvals_exact ON human_approvals(incident_id, action_id, action_version, action_digest)",
        ),
    ),
    Migration(
        2,
        "immutable deterministic triage snapshots",
        (
            """CREATE TABLE triage_snapshots (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE RESTRICT,
                sequence INTEGER NOT NULL CHECK (sequence > 0),
                policy_id TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                matrix_version TEXT NOT NULL,
                policy_checksum TEXT NOT NULL CHECK (length(policy_checksum) = 64),
                input_snapshot_json TEXT NOT NULL CHECK (json_valid(input_snapshot_json)),
                result_snapshot_json TEXT NOT NULL CHECK (json_valid(result_snapshot_json)),
                outcome TEXT NOT NULL CHECK (outcome IN ('COMPLETE','INCOMPLETE')),
                priority TEXT CHECK (priority IN ('P1','P2','P3','P4')),
                recommended_route TEXT CHECK (recommended_route IN ('N1','N2','incident_coordination')),
                escalation_required INTEGER NOT NULL CHECK (escalation_required IN (0,1)),
                missing_evidence_json TEXT NOT NULL CHECK (json_valid(missing_evidence_json)),
                questions_json TEXT NOT NULL CHECK (json_valid(questions_json)),
                risk_signal_ids_json TEXT NOT NULL CHECK (json_valid(risk_signal_ids_json)),
                stop_reason_ids_json TEXT NOT NULL CHECK (json_valid(stop_reason_ids_json)),
                escalation_reason_ids_json TEXT NOT NULL CHECK (json_valid(escalation_reason_ids_json)),
                created_at TEXT NOT NULL,
                created_by TEXT,
                UNIQUE (incident_id, sequence),
                CHECK ((outcome = 'COMPLETE' AND priority IS NOT NULL AND recommended_route IS NOT NULL)
                    OR (outcome = 'INCOMPLETE' AND priority IS NULL AND recommended_route IS NULL))
            )""",
            "CREATE INDEX ix_triage_incident_sequence ON triage_snapshots(incident_id, sequence)",
        ),
    ),
    Migration(
        3,
        "performed procedures and immutable incident documentation",
        (
            """CREATE TABLE performed_procedures (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE RESTRICT,
                sequence INTEGER NOT NULL CHECK (sequence > 0),
                description TEXT NOT NULL CHECK (length(trim(description)) > 0),
                result TEXT NOT NULL CHECK (length(trim(result)) > 0),
                performed_at TEXT NOT NULL,
                actor_reference TEXT NOT NULL CHECK (length(trim(actor_reference)) > 0),
                suggested_action_id TEXT,
                suggested_action_version INTEGER CHECK (suggested_action_version >= 1),
                suggested_action_digest TEXT CHECK (length(suggested_action_digest) = 64),
                CHECK ((suggested_action_id IS NULL AND suggested_action_version IS NULL AND suggested_action_digest IS NULL)
                    OR (suggested_action_id IS NOT NULL AND suggested_action_version IS NOT NULL AND suggested_action_digest IS NOT NULL)),
                UNIQUE (incident_id, sequence)
            )""",
            """CREATE TABLE incident_documentation (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE RESTRICT,
                revision INTEGER NOT NULL CHECK (revision > 0),
                generated_at TEXT NOT NULL,
                generated_by TEXT NOT NULL CHECK (length(trim(generated_by)) > 0),
                document_json TEXT NOT NULL CHECK (json_valid(document_json)),
                UNIQUE (incident_id, revision)
            )""",
            "CREATE INDEX ix_performed_incident_sequence ON performed_procedures(incident_id, sequence)",
            "CREATE INDEX ix_documentation_incident_revision ON incident_documentation(incident_id, revision)",
        ),
    ),
    Migration(
        4,
        "optional operator-declared incident category",
        (
            "ALTER TABLE incidents ADD COLUMN category TEXT CHECK (category IS NULL OR length(trim(category)) > 0)",
            "CREATE INDEX ix_incidents_category_deleted ON incidents(category, deleted_at)",
        ),
    ),
)


def validate_migration_sequence(migrations: tuple[Migration, ...] = MIGRATIONS) -> None:
    versions = [migration.version for migration in migrations]
    if versions != list(range(1, len(versions) + 1)):
        raise ValueError("migration versions must be ordered, unique, and contiguous")
