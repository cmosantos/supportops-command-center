import json
from pathlib import Path

import pytest

from supportops.cli import main
from supportops.config import get_settings


def configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SUPPORTOPS_DB_PATH", str(tmp_path / "triage-cli.db"))
    get_settings.cache_clear()


def create_incident(capsys: pytest.CaptureFixture[str]) -> str:
    assert (
        main(
            [
                "incident",
                "create",
                "--title",
                "Network",
                "--description",
                "Department offline'; DROP TABLE incidents; --",
                "--affected-party",
                "Finance",
                "--affected-service",
                "LAN",
                "--impact",
                "high",
                "--urgency",
                "high",
                "--symptoms",
                "Timeout",
            ]
        )
        == 0
    )
    return str(json.loads(capsys.readouterr().out)["id"])


def complete_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "impact": "high",
        "urgency": "high",
        "affected_scope": "finance department",
        "scope_source": "multiple service desk records",
        "affected_process": "shift processing",
        "process_criticality": "important",
        "workaround_status": "limited",
        "workaround_validation": "tested for some users",
        "business_consequence": "significant delay",
        "containment_status": "stable scope",
        "critical_impact_reassessment": "critical expansion not supported",
        "deadline": "current shift",
        "deadline_owner": "finance lead",
        "delay_consequence": "cutoff missed",
        "time_to_harm": "within hours",
        "condition_stability": "stable",
        "failure_frequency": "continuous",
        "trend": "stable",
        "symptom_context": "timestamped timeout",
        "prior_actions": "read-only checks",
        "recent_change": "none",
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
    return payload


def test_t3_cli_01_to_03_human_json_and_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(monkeypatch, tmp_path)
    assert main(["db", "init"]) == 0
    capsys.readouterr()
    incident_id = create_incident(capsys)
    evidence_json = json.dumps(complete_payload())

    assert (
        main(
            [
                "triage",
                "run",
                incident_id,
                "--evidence-json",
                evidence_json,
                "--actor",
                "analyst-1",
            ]
        )
        == 0
    )
    human = capsys.readouterr().out
    assert "outcome: triage_complete" in human
    assert "priority: P2" in human
    assert "rule: MX-HH" in human
    assert "route: N2" in human
    assert "ESC-02" in human

    assert (
        main(
            [
                "triage",
                "run",
                incident_id,
                "--evidence-json",
                evidence_json,
                "--format",
                "json",
            ]
        )
        == 0
    )
    raw = capsys.readouterr().out
    assert raw.index('"questions"') < raw.index('"priority"')
    machine = json.loads(raw)
    assert machine["outcome"] == "triage_complete"
    assert machine["result"]["policy_id"] == "supportops-triage"
    assert machine["result"]["rule_id"] == "MX-HH"
    assert len(machine["result"]["policy_checksum"]) == 64

    assert main(["triage", "history", incident_id, "--format", "json"]) == 0
    history = json.loads(capsys.readouterr().out)
    assert [item["sequence"] for item in history] == [1, 2]


def test_t3_cli_incomplete_questions_precede_classification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(monkeypatch, tmp_path)
    assert main(["db", "init"]) == 0
    capsys.readouterr()
    incident_id = create_incident(capsys)

    assert (
        main(
            [
                "triage",
                "run",
                incident_id,
                "--evidence-json",
                json.dumps({"symptom_context": "timeout"}),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "outcome: triage_incomplete" in output
    assert output.index("DQ-01") < output.index("classification:")
    assert output.index("DQ-10") < output.index("classification:")
    assert "priority: none" in output
    assert "route: none" in output
    assert "STOP-04" in output


def test_t3_cli_04_deleted_and_unknown_are_hidden(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(monkeypatch, tmp_path)
    assert main(["db", "init"]) == 0
    capsys.readouterr()
    incident_id = create_incident(capsys)
    assert (
        main(["incident", "delete", incident_id, "--reason", "duplicate", "--confirm"])
        == 0
    )
    capsys.readouterr()
    evidence = json.dumps(complete_payload())
    assert main(["triage", "run", incident_id, "--evidence-json", evidence]) == 4
    assert "not found" in capsys.readouterr().out.lower()
    assert (
        main(["triage", "run", "unknown' OR 1=1 --", "--evidence-json", evidence]) == 4
    )
    output = capsys.readouterr().out
    assert "OR 1=1" not in output


def test_invalid_policy_stops_startup_without_secret_or_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    policy = tmp_path / "invalid-policy.json"
    policy.write_text('{"token":"secret-canary"}', encoding="utf-8")
    monkeypatch.setenv("SUPPORTOPS_TRIAGE_POLICY_PATH", str(policy))
    get_settings.cache_clear()
    assert main(["config", "validate"]) == 2
    output = capsys.readouterr().out
    assert "invalid-policy.json" in output
    assert "secret-canary" not in output
    assert str(tmp_path) not in output
    get_settings.cache_clear()
