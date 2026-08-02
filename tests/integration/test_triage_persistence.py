import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from supportops.domain.incidents import Incident, IncidentCreate
from supportops.domain.priority_matrix import Impact, Urgency
from supportops.domain.triage import TriageEvidence, TriageOutcome, TriageResult
from supportops.errors import NotFoundError, PersistenceError
from supportops.lifecycle import IncidentService
from supportops.persistence.database import ConnectionFactory, MigrationRunner
from supportops.repositories import SQLiteTriageRepository
from supportops.triage_policy import load_triage_policy
from supportops.triage_service import TriageService

NOW = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def setup_services(
    path: Path,
) -> tuple[IncidentService, TriageService, ConnectionFactory]:
    factory = ConnectionFactory(path, 200)
    MigrationRunner(factory).apply(NOW.isoformat())
    incidents = IncidentService(factory)
    triage = TriageService(factory, load_triage_policy(), clock=lambda: NOW)
    return incidents, triage, factory


def create_incident(service: IncidentService) -> Incident:
    return service.create(
        IncidentCreate(
            title="Network unavailable",
            description="A department cannot reach the network",
            affected_party="Finance",
            affected_service="LAN",
            impact=Impact.HIGH,
            urgency=Urgency.HIGH,
            symptoms="Connection timeout",
            error_messages=("timeout",),
            actions_already_taken=("checked service status",),
            actor_reference="analyst-1",
        )
    )


def complete_evidence(**changes: object) -> TriageEvidence:
    payload: dict[str, object] = {
        "impact": "high",
        "urgency": "high",
        "affected_scope": "finance department",
        "scope_source": "service desk corroboration",
        "affected_process": "current shift processing",
        "process_criticality": "important",
        "workaround_status": "limited",
        "workaround_validation": "tested for some users",
        "business_consequence": "significant processing delay",
        "containment_status": "scope stable",
        "critical_impact_reassessment": "critical expansion not supported",
        "deadline": "current shift",
        "deadline_owner": "finance lead",
        "delay_consequence": "processing cutoff missed",
        "time_to_harm": "within hours",
        "condition_stability": "stable",
        "failure_frequency": "continuous",
        "trend": "stable",
        "symptom_context": "timestamped timeout from managed endpoint",
        "prior_actions": "read-only checks completed",
        "recent_change": "none identified",
        "corroboration": "multiple tickets",
        "risk_assessment_status": "none_identified",
        "requires_admin_or_change": False,
        "within_approved_runbook_or_noninvasive": True,
        "n1_safe_boundary": True,
        "expected_result_defined": True,
        "stop_condition_defined": True,
    }
    payload.update(changes)
    payload.setdefault("supported_impact_criteria", [payload.get("impact")])
    payload.setdefault("supported_urgency_criteria", [payload.get("urgency")])
    return TriageEvidence.model_validate(payload)


def test_t3_int_01_snapshot_and_questions_round_trip_atomically(
    tmp_path: Path,
) -> None:
    incidents, triage, factory = setup_services(tmp_path / "roundtrip.db")
    incident = create_incident(incidents)

    result = triage.triage(incident.id, complete_evidence(), "analyst-2")
    assert result.sequence == 1
    assert result.outcome is TriageOutcome.COMPLETE
    assert result.policy_checksum == load_triage_policy().checksum
    assert triage.history(incident.id) == (result,)

    connection = factory.connect()
    try:
        row = connection.execute(
            "SELECT outcome,priority,recommended_route,questions_json "
            "FROM triage_snapshots WHERE incident_id = ?",
            (incident.id,),
        ).fetchone()
        assert tuple(row) == ("COMPLETE", "P2", "N2", "[]")
    finally:
        connection.close()


def test_t3_int_02_retriage_appends_and_preserves_prior_snapshot(
    tmp_path: Path,
) -> None:
    incidents, triage, _ = setup_services(tmp_path / "retriage.db")
    incident = create_incident(incidents)
    first = triage.triage(incident.id, complete_evidence(), "analyst-1")
    second = triage.triage(
        incident.id,
        complete_evidence(
            impact="critical",
            urgency="critical",
            business_consequence="mission-critical work stopped",
            containment_status="no containment",
            workaround_status="none",
            time_to_harm="active now",
        ),
        "analyst-2",
    )

    history = triage.history(incident.id)
    assert history == (first, second)
    assert [item.sequence for item in history] == [1, 2]
    assert [item.priority.value for item in history if item.priority] == ["P2", "P1"]
    assert first.policy_checksum == second.policy_checksum
    assert first.snapshot_id != second.snapshot_id


def test_deleted_and_unknown_incidents_are_not_triaged(tmp_path: Path) -> None:
    incidents, triage, factory = setup_services(tmp_path / "hidden.db")
    incident = create_incident(incidents)
    incidents.soft_delete(incident.id, "duplicate", True)

    for incident_id in (incident.id, "missing"):
        with pytest.raises(NotFoundError):
            triage.triage(incident_id, complete_evidence())
        with pytest.raises(NotFoundError):
            triage.history(incident_id)

    connection = factory.connect()
    try:
        assert (
            connection.execute("SELECT count(*) FROM triage_snapshots").fetchone()[0]
            == 0
        )
    finally:
        connection.close()


def test_injected_failure_after_snapshot_insert_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    incidents, triage, factory = setup_services(tmp_path / "rollback.db")
    incident = create_incident(incidents)
    original = SQLiteTriageRepository.add

    def fail_after_insert(
        self: SQLiteTriageRepository, result: TriageResult
    ) -> TriageResult:
        original(self, result)
        raise sqlite3.IntegrityError("injected after snapshot insert")

    monkeypatch.setattr(SQLiteTriageRepository, "add", fail_after_insert)
    with pytest.raises(PersistenceError) as captured:
        triage.triage(incident.id, complete_evidence())
    assert "injected" not in captured.value.public_message

    connection = factory.connect()
    try:
        assert (
            connection.execute("SELECT count(*) FROM triage_snapshots").fetchone()[0]
            == 0
        )
    finally:
        connection.close()


def test_foreign_key_rejects_orphan_triage_snapshot(tmp_path: Path) -> None:
    _, _, factory = setup_services(tmp_path / "foreign-key-triage.db")
    connection = factory.connect()
    try:
        connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO triage_snapshots("
                "id,incident_id,sequence,policy_id,schema_version,matrix_version,"
                "policy_checksum,input_snapshot_json,result_snapshot_json,outcome,"
                "priority,recommended_route,escalation_required,missing_evidence_json,"
                "questions_json,risk_signal_ids_json,stop_reason_ids_json,"
                "escalation_reason_ids_json,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "snapshot-orphan",
                    "incident-missing",
                    1,
                    "supportops-triage",
                    "1",
                    "test",
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
                    NOW.isoformat(),
                ),
            )
        connection.rollback()
        assert (
            connection.execute("SELECT count(*) FROM triage_snapshots").fetchone()[0]
            == 0
        )
    finally:
        connection.close()


def test_repository_exposes_no_snapshot_update_or_delete() -> None:
    assert not hasattr(SQLiteTriageRepository, "update")
    assert not hasattr(SQLiteTriageRepository, "delete")


def test_stop_outcome_does_not_mutate_lifecycle_or_approvals(tmp_path: Path) -> None:
    incidents, triage, factory = setup_services(tmp_path / "stop-no-side-effects.db")
    incident = create_incident(incidents)
    result = triage.triage(
        incident.id,
        complete_evidence(
            risk_assessment_status="confirmed",
            risk_signal_ids=["security_compromise"],
            next_step_administrative=True,
        ),
    )
    assert result.stop.required
    assert result.stop.reason_ids == ("STOP-01", "STOP-02")
    assert incidents.get(incident.id).status.value == "OPEN"
    assert [event.event_type for event in incidents.history(incident.id)] == [
        "INCIDENT_CREATED"
    ]
    connection = factory.connect()
    try:
        assert (
            connection.execute("SELECT count(*) FROM human_approvals").fetchone()[0]
            == 0
        )
    finally:
        connection.close()
