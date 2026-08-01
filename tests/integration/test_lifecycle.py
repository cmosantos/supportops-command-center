import hashlib
import sqlite3
from pathlib import Path

import pytest

from supportops.domain.incidents import (
    ApprovalDecision,
    ApprovalInput,
    IncidentCreate,
    IncidentStatus,
    IncidentUpdate,
)
from supportops.domain.priority_matrix import Impact, Urgency
from supportops.errors import (
    ConflictError,
    InputValidationError,
    InvalidTransitionError,
    NotFoundError,
    PersistenceError,
)
from supportops.lifecycle import IncidentService, canonical_snapshot
from supportops.persistence.database import ConnectionFactory, MigrationRunner
from supportops.repositories import SQLiteIncidentRepository


def setup_service(
    path: Path, timeout: int = 200
) -> tuple[IncidentService, ConnectionFactory]:
    factory = ConnectionFactory(path, timeout)
    MigrationRunner(factory).apply("2026-08-01T00:00:00+00:00")
    return IncidentService(factory), factory


def incident_input(title: str = "Network issue") -> IncidentCreate:
    return IncidentCreate(
        title=title,
        description="Cannot reach the internal service",
        affected_party="Finance",
        affected_service="LAN",
        impact=Impact.MODERATE,
        urgency=Urgency.HIGH,
        symptoms="Connection timeout",
        error_messages=("timeout",),
        actions_already_taken=("checked cable",),
        actor_reference="analyst-1",
    )


def test_create_round_trip_update_and_history_are_atomic(tmp_path: Path) -> None:
    service, _ = setup_service(tmp_path / "lifecycle.db")
    created = service.create(incident_input("quote ' and ; payload"))

    assert service.get(created.id) == created
    updated = service.update(
        created.id, IncidentUpdate(expected_version=1, title="Updated")
    )
    assert updated.title == "Updated"
    assert updated.version == 2
    assert [event.event_type for event in service.history(created.id)] == [
        "INCIDENT_CREATED",
        "INCIDENT_UPDATED",
    ]

    with pytest.raises(ConflictError):
        service.update(created.id, IncidentUpdate(expected_version=1, title="stale"))
    assert service.get(created.id).title == "Updated"
    assert len(service.history(created.id)) == 2


def test_close_reopen_cycles_preserve_history_and_latest_close(tmp_path: Path) -> None:
    service, _ = setup_service(tmp_path / "cycles.db")
    created = service.create(incident_input())
    first_closed = service.close(created.id)
    assert first_closed.status is IncidentStatus.CLOSED
    assert first_closed.closed_at is not None
    assert first_closed.handling_seconds is not None

    with pytest.raises(InvalidTransitionError):
        service.close(created.id)
    reopened = service.reopen(created.id)
    assert reopened.status is IncidentStatus.OPEN
    assert reopened.closed_at is None
    second_closed = service.close(created.id)
    assert second_closed.closed_at is not None
    assert [event.event_type for event in service.history(created.id)] == [
        "INCIDENT_CREATED",
        "INCIDENT_CLOSED",
        "INCIDENT_OPEN",
        "INCIDENT_CLOSED",
    ]


def test_soft_delete_is_hidden_but_audit_data_remains(tmp_path: Path) -> None:
    service, factory = setup_service(tmp_path / "deleted.db")
    created = service.create(incident_input())

    service.soft_delete(created.id, "duplicate incident", True, "analyst-2")
    with pytest.raises(NotFoundError):
        service.get(created.id)
    assert service.list() == ()
    with pytest.raises(NotFoundError):
        service.close(created.id)

    connection = factory.connect()
    try:
        deleted = SQLiteIncidentRepository(connection).get(
            created.id, include_deleted=True
        )
        assert deleted is not None
        assert deleted.deletion_confirmed is True
        assert deleted.deletion_reason == "duplicate incident"
        assert deleted.pre_deletion_status is IncidentStatus.OPEN
        assert len(SQLiteIncidentRepository(connection).history(created.id)) == 2
    finally:
        connection.close()


def test_approval_binding_requires_exact_snapshot_and_incident(tmp_path: Path) -> None:
    service, _ = setup_service(tmp_path / "approval.db")
    first = service.create(incident_input("first"))
    second = service.create(incident_input("second"))
    snapshot = {"command": "Get-Service", "risk": "low"}
    digest = hashlib.sha256(canonical_snapshot(snapshot).encode()).hexdigest()
    approval = service.record_approval(
        ApprovalInput(
            incident_id=first.id,
            action_id="action-1",
            action_version=1,
            action_digest=digest,
            action_snapshot=snapshot,
            decision=ApprovalDecision.APPROVED,
            approver_reference="declared-manager",
            note="identity is not authenticated",
        )
    )

    assert approval.action_snapshot == snapshot
    assert service.approval_matches(first.id, "action-1", 1, digest)
    assert not service.approval_matches(first.id, "action-1", 2, digest)
    assert not service.approval_matches(second.id, "action-1", 1, digest)
    changed = hashlib.sha256(
        canonical_snapshot({"command": "other"}).encode()
    ).hexdigest()
    assert not service.approval_matches(first.id, "action-1", 1, changed)
    assert service.history(first.id)[-1].event_type == "APPROVAL_RECORDED"


def test_controlled_lock_maps_to_safe_error(tmp_path: Path) -> None:
    service, factory = setup_service(tmp_path / "locked.db", timeout=100)
    lock = factory.connect()
    lock.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(PersistenceError) as captured:
            service.create(incident_input())
        assert "locked" not in captured.value.public_message.lower()
        assert str(factory.path) not in captured.value.public_message
    finally:
        lock.rollback()
        lock.close()


def test_invalid_approval_digest_rolls_back_without_event(tmp_path: Path) -> None:
    service, _ = setup_service(tmp_path / "bad-approval.db")
    incident = service.create(incident_input())
    before = service.history(incident.id)

    with pytest.raises(InputValidationError):
        service.record_approval(
            ApprovalInput(
                incident_id=incident.id,
                action_id="action-1",
                action_version=1,
                action_digest="0" * 64,
                action_snapshot={"command": "Get-Service"},
                decision=ApprovalDecision.REJECTED,
                approver_reference="declared-manager",
            )
        )

    assert service.history(incident.id) == before


def test_event_sequence_is_deterministic_with_fixed_clock_and_adversarial_ids(
    tmp_path: Path,
) -> None:
    fixed = __import__("datetime").datetime(
        2026, 8, 1, tzinfo=__import__("datetime").UTC
    )
    identifiers = iter(("incident-z", "event-z", "event-a", "event-m"))
    factory = ConnectionFactory(tmp_path / "sequence.db", 200)
    MigrationRunner(factory).apply(fixed.isoformat())
    service = IncidentService(
        factory, clock=lambda: fixed, id_generator=lambda: next(identifiers)
    )

    incident = service.create(incident_input())
    service.close(incident.id)
    service.reopen(incident.id)
    history = service.history(incident.id)

    assert [event.id for event in history] == ["event-z", "event-a", "event-m"]
    assert [event.sequence for event in history] == [1, 2, 3]
    assert [event.event_type for event in history] == [
        "INCIDENT_CREATED",
        "INCIDENT_CLOSED",
        "INCIDENT_OPEN",
    ]


@pytest.mark.parametrize(
    "decision", [ApprovalDecision.PENDING, ApprovalDecision.REJECTED]
)
def test_non_approved_decisions_never_match(
    tmp_path: Path, decision: ApprovalDecision
) -> None:
    service, _ = setup_service(tmp_path / f"{decision.value}.db")
    incident = service.create(incident_input())
    snapshot = {"command": "Get-Service"}
    digest = hashlib.sha256(canonical_snapshot(snapshot).encode()).hexdigest()
    service.record_approval(
        ApprovalInput(
            incident_id=incident.id,
            action_id="action-non-approved",
            action_version=1,
            action_digest=digest,
            action_snapshot=snapshot,
            decision=decision,
            approver_reference="declared-manager",
        )
    )

    assert not service.approval_matches(incident.id, "action-non-approved", 1, digest)


def test_fault_after_projection_mutation_rolls_back_projection_and_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, _ = setup_service(tmp_path / "fault.db")
    incident = service.create(incident_input())
    history_before = service.history(incident.id)

    def fail_event(self: SQLiteIncidentRepository, event: object) -> None:
        raise sqlite3.IntegrityError("injected after projection mutation")

    monkeypatch.setattr(SQLiteIncidentRepository, "append_event", fail_event)
    with pytest.raises(PersistenceError):
        service.update(
            incident.id,
            IncidentUpdate(expected_version=1, title="must rollback"),
        )

    current = service.get(incident.id)
    assert current.title == incident.title
    assert current.version == incident.version
    assert service.history(incident.id) == history_before
