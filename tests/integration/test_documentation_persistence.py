from datetime import UTC, datetime
from pathlib import Path

import pytest

from supportops.documentation_service import NEUTRAL, DocumentationService
from supportops.domain.documentation import ExportFormat, PerformedProcedureInput
from supportops.domain.incidents import IncidentCreate
from supportops.domain.priority_matrix import Impact, Urgency
from supportops.errors import (
    ConflictError,
    InputValidationError,
    NotFoundError,
    PersistenceError,
)
from supportops.exporters import (
    ContainedExportWriter,
    JsonIncidentExporter,
    MarkdownIncidentExporter,
)
from supportops.lifecycle import IncidentService
from supportops.persistence.database import ConnectionFactory, MigrationRunner


def setup(tmp_path: Path) -> tuple[IncidentService, DocumentationService]:
    factory = ConnectionFactory(tmp_path / "db.sqlite", 200)
    MigrationRunner(factory).apply("2026-08-02T00:00:00+00:00")
    ids = iter(f"id-{number}" for number in range(50))

    def clock() -> datetime:
        return datetime(2026, 8, 2, tzinfo=UTC)

    lifecycle = IncidentService(factory, clock=clock, id_generator=lambda: next(ids))
    documentation = DocumentationService(
        factory,
        ContainedExportWriter(tmp_path / "exports"),
        {
            ExportFormat.MARKDOWN: MarkdownIncidentExporter(),
            ExportFormat.JSON: JsonIncidentExporter(),
        },
        clock=clock,
        id_generator=lambda: next(ids),
    )
    return lifecycle, documentation


def create(lifecycle: IncidentService) -> str:
    return lifecycle.create(
        IncidentCreate(
            title="OneDrive",
            description="Client stopped",
            affected_party="User A",
            affected_service="OneDrive",
            impact=Impact.LOW,
            urgency=Urgency.MODERATE,
            symptoms="No synchronization",
            error_messages=("0x1",),
            actor_reference="n1",
        )
    ).id


def test_performed_and_revision_history_are_separate_and_ordered(
    tmp_path: Path,
) -> None:
    lifecycle, service = setup(tmp_path)
    incident_id = create(lifecycle)
    first = service.record_performed(
        incident_id,
        PerformedProcedureInput(
            description="Checked client state",
            result="Client paused",
            actor_reference="n1",
        ),
    )
    second = service.record_performed(
        incident_id,
        PerformedProcedureInput(
            description="Resumed client", result="Sync restored", actor_reference="n2"
        ),
    )
    assert (first.sequence, second.sequence) == (1, 2)
    revision1 = service.generate(incident_id, "n2")
    revision2 = service.generate(incident_id, "n2")
    assert (revision1.revision, revision2.revision) == (1, 2)
    assert len(revision2.sections.performed_procedures) == 2
    assert revision2.sections.suggested_procedures == (NEUTRAL,)
    assert [item.revision for item in service.history(incident_id)] == [1, 2]


def test_cross_incident_action_reference_is_rejected_atomically(tmp_path: Path) -> None:
    lifecycle, service = setup(tmp_path)
    incident_id = create(lifecycle)
    with pytest.raises(InputValidationError):
        service.record_performed(
            incident_id,
            PerformedProcedureInput(
                description="reported",
                result="result",
                actor_reference="n1",
                suggested_action_id="unknown",
                suggested_action_version=1,
                suggested_action_digest="0" * 64,
            ),
        )
    assert service.list_performed(incident_id) == ()


def test_deleted_and_missing_document_are_excluded(tmp_path: Path) -> None:
    lifecycle, service = setup(tmp_path)
    incident_id = create(lifecycle)
    with pytest.raises(NotFoundError):
        service.get(incident_id)
    lifecycle.soft_delete(incident_id, "duplicate", True)
    with pytest.raises(NotFoundError):
        service.generate(incident_id, "n1")


def test_export_both_formats_and_collision_preserves_existing(tmp_path: Path) -> None:
    lifecycle, service = setup(tmp_path)
    incident_id = create(lifecycle)
    service.generate(incident_id, "n1")
    markdown = service.export(incident_id, ExportFormat.MARKDOWN)
    json_export = service.export(incident_id, ExportFormat.JSON)
    assert (tmp_path / "exports" / markdown.relative_path).is_file()
    assert (tmp_path / "exports" / json_export.relative_path).is_file()
    with pytest.raises(ConflictError):
        service.export(incident_id, ExportFormat.JSON)


def test_corrupt_persisted_approval_triage_and_document_fail_safely(
    tmp_path: Path,
) -> None:
    lifecycle, service = setup(tmp_path)
    incident_id = create(lifecycle)
    connection = service.factory.connect()
    connection.execute(
        "INSERT INTO human_approvals VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "a",
            incident_id,
            "act",
            1,
            "0" * 64,
            "{",
            "APPROVED",
            "n1",
            "2026-08-02T00:00:00+00:00",
            None,
            "2026-08-02T00:00:00+00:00",
        ),
    )
    connection.close()
    with pytest.raises(PersistenceError):
        service.generate(incident_id, "n1")

    connection = service.factory.connect()
    connection.execute("DELETE FROM human_approvals")
    connection.execute(
        "INSERT INTO triage_snapshots(id,incident_id,sequence,policy_id,schema_version,"
        "matrix_version,policy_checksum,input_snapshot_json,result_snapshot_json,outcome,"
        "priority,recommended_route,escalation_required,missing_evidence_json,questions_json,"
        "risk_signal_ids_json,stop_reason_ids_json,escalation_reason_ids_json,"
        "created_at,created_by) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "t",
            incident_id,
            1,
            "p",
            "1",
            "m",
            "0" * 64,
            "{}",
            "{}",
            "INCOMPLETE",
            None,
            None,
            0,
            "[]",
            "[]",
            "[]",
            "[]",
            "[]",
            "2026-08-02T00:00:00+00:00",
            "n1",
        ),
    )
    connection.close()
    with pytest.raises(PersistenceError):
        service.generate(incident_id, "n1")

    connection = service.factory.connect()
    connection.execute("DELETE FROM triage_snapshots")
    connection.execute(
        "INSERT INTO incident_documentation VALUES (?,?,?,?,?,?)",
        ("bad", incident_id, 1, "2026-08-02T00:00:00+00:00", "n1", "{}"),
    )
    connection.close()
    with pytest.raises(PersistenceError):
        service.history(incident_id)
    with pytest.raises(PersistenceError):
        service.get(incident_id, 1)


def test_invalid_clock_and_corrupt_performed_row_fail_safely(tmp_path: Path) -> None:
    lifecycle, service = setup(tmp_path)
    incident_id = create(lifecycle)
    invalid_clock_service = DocumentationService(
        service.factory,
        service.writer,
        service.exporters,
        clock=lambda: datetime(2026, 8, 2),
        id_generator=lambda: "invalid-clock",
    )
    with pytest.raises(PersistenceError):
        invalid_clock_service.record_performed(
            incident_id,
            PerformedProcedureInput(
                description="reported", result="result", actor_reference="n1"
            ),
        )
    assert service.list_performed(incident_id) == ()

    connection = service.factory.connect()
    connection.execute(
        "INSERT INTO performed_procedures(id,incident_id,sequence,description,result,"
        "performed_at,actor_reference,suggested_action_id,suggested_action_version,"
        "suggested_action_digest) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "bad",
            incident_id,
            1,
            "reported",
            "result",
            "2026-08-02T00:00:00+01:00",
            "n1",
            None,
            None,
            None,
        ),
    )
    connection.close()
    with pytest.raises(PersistenceError):
        service.list_performed(incident_id)
