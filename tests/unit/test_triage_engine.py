from datetime import UTC, datetime
from itertools import product

import pytest
from pydantic import ValidationError

from supportops.domain.priority_matrix import Impact, Priority, Urgency
from supportops.domain.triage import (
    ConditionalEscalationTrigger,
    RiskAssessmentStatus,
    SupportRoute,
    TriageEvidence,
    TriageOutcome,
    TriageResult,
)
from supportops.triage_engine import evaluate_triage
from supportops.triage_policy import load_triage_policy

NOW = datetime(2026, 8, 1, tzinfo=UTC)


def complete_evidence(**changes: object) -> TriageEvidence:
    values: dict[str, object] = {
        "impact": "low",
        "urgency": "low",
        "affected_scope": "one user",
        "scope_source": "service desk query",
        "affected_process": "email access",
        "process_criticality": "non-critical",
        "workaround_status": "viable",
        "workaround_validation": "tested",
        "business_consequence": "limited rework",
        "containment_status": "contained",
        "critical_impact_reassessment": "critical expansion not supported",
        "deadline": "next business day",
        "deadline_owner": "operations lead",
        "delay_consequence": "minor delay",
        "time_to_harm": "more than one day",
        "condition_stability": "stable",
        "failure_frequency": "continuous",
        "trend": "stable",
        "symptom_context": "exact error captured on workstation",
        "prior_actions": "read-only checks recorded",
        "recent_change": "none identified",
        "corroboration": "no related alerts",
        "risk_assessment_status": "none_identified",
        "requires_admin_or_change": False,
        "within_approved_runbook_or_noninvasive": True,
        "n1_safe_boundary": True,
        "expected_result_defined": True,
        "stop_condition_defined": True,
    }
    values.update(changes)
    values.setdefault("supported_impact_criteria", [values.get("impact")])
    values.setdefault("supported_urgency_criteria", [values.get("urgency")])
    return TriageEvidence.model_validate(values)


def evaluate(evidence: TriageEvidence) -> TriageResult:
    return evaluate_triage(
        load_triage_policy(),
        evidence,
        incident_id="incident-1",
        snapshot_id="snapshot-1",
        generated_at=NOW,
        created_by="analyst-1",
    )


@pytest.mark.parametrize(
    ("impact", "urgency", "priority", "rule_id"),
    [
        (rule.impact, rule.urgency, rule.priority, rule.rule_id)
        for rule in load_triage_policy().matrix_rules
    ],
    ids=[f"T3-MX-{index:02d}" for index in range(1, 17)],
)
def test_all_matrix_cells(
    impact: Impact, urgency: Urgency, priority: Priority, rule_id: str
) -> None:
    result = evaluate(complete_evidence(impact=impact, urgency=urgency))
    assert result.outcome is TriageOutcome.COMPLETE
    assert result.priority is priority
    assert result.rule_id == rule_id


@pytest.mark.parametrize(
    "impact", list(Impact), ids=[f"T3-IMP-{i:02d}" for i in range(1, 5)]
)
def test_each_impact_accepts_required_evidence(impact: Impact) -> None:
    assert evaluate(complete_evidence(impact=impact)).impact is impact


def test_t3_imp_05_highest_supported_impact_wins() -> None:
    result = evaluate(
        complete_evidence(
            impact=None,
            supported_impact_criteria=["low", "moderate", "critical"],
            symptom_context="CEO says this is low",
        )
    )
    assert result.outcome is TriageOutcome.COMPLETE
    assert result.impact is Impact.CRITICAL


def test_declared_impact_conflicting_with_supported_criteria_is_incomplete() -> None:
    result = evaluate(
        complete_evidence(
            impact="critical",
            supported_impact_criteria=["low"],
            affected_scope="one user",
            business_consequence="minor",
            containment_status="contained",
        )
    )
    assert result.outcome is TriageOutcome.INCOMPLETE
    assert result.priority is None
    assert "contradiction:impact" in result.missing_evidence


@pytest.mark.parametrize(
    "urgency", list(Urgency), ids=[f"T3-URG-{i:02d}" for i in range(1, 5)]
)
def test_each_urgency_accepts_required_evidence(urgency: Urgency) -> None:
    assert evaluate(complete_evidence(urgency=urgency)).urgency is urgency


def test_t3_urg_05_highest_supported_urgency_wins_and_text_is_ignored() -> None:
    result = evaluate(
        complete_evidence(
            urgency=None,
            supported_urgency_criteria=["low", "high"],
            symptom_context="requester says low but URGENT NOW CRITICAL",
        )
    )
    assert result.outcome is TriageOutcome.COMPLETE
    assert result.urgency is Urgency.HIGH


@pytest.mark.parametrize(
    ("changes", "reason", "route"),
    [
        (
            {"impact": "critical", "urgency": "critical"},
            "ESC-01",
            "incident_coordination",
        ),
        ({"impact": "high"}, "ESC-02", "N2"),
        (
            {
                "risk_assessment_status": "suspected",
                "risk_signal_ids": ["security_compromise"],
            },
            "ESC-03",
            "incident_coordination",
        ),
        ({"requires_admin_or_change": True}, "ESC-04", "N2"),
        ({"cross_team_or_vendor": True}, "ESC-05", "incident_coordination"),
        ({"n1_checks_exhausted": True}, "ESC-06", "N2"),
    ],
    ids=[f"T3-ESC-{i:02d}" for i in range(1, 7)],
)
def test_each_escalation_rule(
    changes: dict[str, object], reason: str, route: str
) -> None:
    result = evaluate(complete_evidence(**changes))
    assert reason in result.escalation_reason_ids
    assert result.recommended_route == route


def test_t3_esc_07_and_13_reasons_add_and_highest_route_wins() -> None:
    result = evaluate(
        complete_evidence(
            impact="critical",
            urgency="critical",
            risk_assessment_status="confirmed",
            risk_signal_ids=["data_integrity_loss"],
            requires_admin_or_change=True,
            cross_team_or_vendor=True,
        )
    )
    assert result.escalation_reason_ids == (
        "ESC-01",
        "ESC-02",
        "ESC-03",
        "ESC-04",
        "ESC-05",
    )
    assert result.recommended_route is SupportRoute.INCIDENT_COORDINATION


@pytest.mark.parametrize(
    ("impact", "urgency", "route"),
    [
        ("low", "high", "N2"),
        ("moderate", "moderate", "N2"),
        ("moderate", "high", "incident_coordination"),
    ],
    ids=["T3-ESC-09", "T3-ESC-10", "T3-ESC-11"],
)
def test_conditional_escalation_routes(impact: str, urgency: str, route: str) -> None:
    result = evaluate(
        complete_evidence(
            impact=impact,
            urgency=urgency,
            conditional_triggers=[ConditionalEscalationTrigger.BASELINE_LIMIT_REACHED],
        )
    )
    assert result.recommended_route == route
    assert result.escalation_required
    assert result.escalation_reason_ids == (
        f"COND-{result.rule_id}-baseline_limit_reached",
    )


def test_conditional_escalation_retains_every_trigger_reason() -> None:
    result = evaluate(
        complete_evidence(
            impact="low",
            urgency="high",
            conditional_triggers=[
                "baseline_limit_reached",
                "logs_inaccessible",
            ],
        )
    )
    assert result.escalation_required
    assert result.escalation_reason_ids == (
        "COND-MX-LH-baseline_limit_reached",
        "COND-MX-LH-logs_inaccessible",
    )


def test_t3_esc_12_conditional_does_not_bypass_mandatory_route() -> None:
    result = evaluate(
        complete_evidence(
            impact="moderate",
            urgency="high",
            conditional_triggers=["runbook_unavailable"],
            cross_team_or_vendor=True,
        )
    )
    assert result.recommended_route is SupportRoute.INCIDENT_COORDINATION
    assert "ESC-05" in result.escalation_reason_ids


def test_t3_lvl_01_n1_requires_all_conditions() -> None:
    assert evaluate(complete_evidence()).recommended_route is SupportRoute.N1


@pytest.mark.parametrize(
    "field",
    [
        "within_approved_runbook_or_noninvasive",
        "n1_safe_boundary",
        "expected_result_defined",
        "stop_condition_defined",
    ],
    ids=["T3-LVL-02a", "T3-LVL-02b", "T3-LVL-02c", "T3-LVL-02d"],
)
def test_t3_lvl_02_failed_n1_condition_routes_n2(field: str) -> None:
    assert (
        evaluate(complete_evidence(**{field: False})).recommended_route
        is SupportRoute.N2
    )


def test_t3_risk_01_to_04_valid_status_contract() -> None:
    assert (
        complete_evidence(risk_assessment_status="not_assessed").risk_signal_ids == ()
    )
    assert (
        complete_evidence(risk_assessment_status="none_identified").risk_signal_ids
        == ()
    )
    for status in ("suspected", "confirmed"):
        evidence = complete_evidence(
            risk_assessment_status=status,
            risk_signal_ids=["privacy_exposure"],
        )
        assert evidence.risk_signal_ids


@pytest.mark.parametrize(
    "payload",
    [
        {
            "risk_assessment_status": "none_identified",
            "risk_signal_ids": ["privacy_exposure"],
        },
        {"risk_assessment_status": "suspected", "risk_signal_ids": []},
        {"risk_assessment_status": "suspected", "risk_signal_ids": ["unknown"]},
        {
            "risk_assessment_status": "confirmed",
            "risk_signal_ids": ["privacy_exposure", "privacy_exposure"],
        },
    ],
    ids=[
        "T3-RISK-03-pair",
        "T3-RISK-04-pair",
        "T3-RISK-05-unknown",
        "T3-RISK-06-duplicate",
    ],
)
def test_invalid_risk_pairs_are_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        complete_evidence(**payload)


def test_free_text_cannot_infer_risk() -> None:
    result = evaluate(
        complete_evidence(
            risk_assessment_status=RiskAssessmentStatus.NONE_IDENTIFIED,
            symptom_context="credential exposure security compromise",
        )
    )
    assert "ESC-03" not in result.escalation_reason_ids
    assert "STOP-01" not in result.stop.reason_ids


def test_t3_gap_and_dq_incomplete_has_no_classification() -> None:
    evidence = TriageEvidence(symptom_context="only free text")
    result = evaluate(evidence)
    assert result.outcome is TriageOutcome.INCOMPLETE
    assert result.priority is None
    assert result.recommended_route is None
    question_ids = [question.question_id for question in result.questions]
    assert "DQ-01" in question_ids
    assert "DQ-04" in question_ids
    assert "DQ-10" in {question.question_id for question in result.questions}
    assert len({question.question_id for question in result.questions}) == len(
        result.questions
    )
    assert result.stop.reason_ids == ("STOP-04",)


@pytest.mark.parametrize(
    ("changes", "stop_id"),
    [
        (
            {
                "risk_assessment_status": "suspected",
                "risk_signal_ids": ["security_compromise"],
            },
            "STOP-01",
        ),
        ({"next_step_destructive": True}, "STOP-02"),
        ({"scope_increasing": True}, "STOP-03"),
        ({"evidence_conflicts": ["scope"]}, "STOP-04"),
        ({"controlled_attempts": 2}, "STOP-05"),
        ({"ownership_or_recovery_unknown": True}, "STOP-06"),
        ({"major_incident_procedure": True}, "STOP-07"),
    ],
    ids=[f"T3-STOP-{i:02d}" for i in range(1, 8)],
)
def test_each_stop_rule(changes: dict[str, object], stop_id: str) -> None:
    result = evaluate(complete_evidence(**changes))
    assert result.stop.required
    assert stop_id in result.stop.reason_ids


def test_all_impact_urgency_combinations_repeat_identically() -> None:
    for impact, urgency in product(Impact, Urgency):
        evidence = complete_evidence(impact=impact, urgency=urgency)
        assert evaluate(evidence).model_copy(update={"snapshot_id": "x"}).model_dump(
            exclude={"snapshot_id"}
        ) == evaluate(evidence).model_copy(update={"snapshot_id": "y"}).model_dump(
            exclude={"snapshot_id"}
        )


@pytest.mark.parametrize(
    ("changes", "question_id"),
    [
        ({"affected_scope": None}, "DQ-01"),
        ({"affected_process": None}, "DQ-02"),
        ({"workaround_status": None}, "DQ-03"),
        ({"deadline": None}, "DQ-04"),
        ({"condition_stability": None, "failure_frequency": None}, "DQ-05"),
        ({"symptom_context": None}, "DQ-06"),
        ({"prior_actions": None}, "DQ-07"),
        ({"recent_change": None}, "DQ-08"),
        ({"corroboration": None}, "DQ-09"),
        ({"risk_assessment_status": "not_assessed"}, "DQ-10"),
        ({"requires_admin_or_change": None}, "DQ-11"),
        (
            {"controlled_test_considered": True, "safe_reproduction_criteria": None},
            "DQ-12",
        ),
    ],
    ids=[f"T3-DQ-{index:02d}" for index in range(1, 13)],
)
def test_each_diagnostic_question_is_condition_driven(
    changes: dict[str, object], question_id: str
) -> None:
    result = evaluate(complete_evidence(impact="high", urgency="high", **changes))
    assert question_id in {question.question_id for question in result.questions}


def test_answered_facts_are_not_requested_again() -> None:
    result = evaluate(complete_evidence())
    assert result.questions == ()


def test_escalation_never_reduces_matrix_priority() -> None:
    result = evaluate(
        complete_evidence(
            impact="high",
            urgency="high",
            risk_assessment_status="confirmed",
            risk_signal_ids=["data_integrity_loss"],
        )
    )
    assert result.priority is Priority.P2
    assert result.recommended_route is SupportRoute.INCIDENT_COORDINATION


@pytest.mark.parametrize(
    ("changes", "question_id"),
    [
        ({"process_criticality": None}, "DQ-02"),
        ({"workaround_validation": None}, "DQ-03"),
        ({"time_to_harm": None}, "DQ-05"),
        ({"cause_materially_uncertain": True}, "DQ-08"),
        (
            {"multi_user_or_scope_suspected": True, "corroboration": None},
            "DQ-09",
        ),
    ],
    ids=[
        "T3-DQ-02-criticality",
        "T3-DQ-03-high-workaround",
        "T3-DQ-05-time-to-harm",
        "T3-DQ-08-uncertain-cause",
        "T3-DQ-09-multi-user",
    ],
)
def test_documented_dq_boundary_conditions(
    changes: dict[str, object], question_id: str
) -> None:
    result = evaluate(complete_evidence(impact="high", urgency="high", **changes))
    assert question_id in {question.question_id for question in result.questions}


def test_labels_without_supported_criteria_never_classify() -> None:
    evidence = complete_evidence(
        impact="critical",
        urgency="critical",
        supported_impact_criteria=[],
        supported_urgency_criteria=[],
        affected_scope="one user",
        business_consequence="minor",
        containment_status="contained",
    )
    result = evaluate(evidence)
    assert result.outcome is TriageOutcome.INCOMPLETE
    assert result.impact is None
    assert result.urgency is None
    assert result.priority is None
    assert result.recommended_route is None


@pytest.mark.parametrize(
    "changes",
    [
        {"process_criticality": None},
        {"workaround_validation": None},
    ],
    ids=["T3-BLOCK-DQ02", "T3-BLOCK-DQ03"],
)
def test_any_blocking_question_forces_incomplete_and_stop(
    changes: dict[str, object],
) -> None:
    result = evaluate(complete_evidence(impact="high", urgency="high", **changes))
    assert result.outcome is TriageOutcome.INCOMPLETE
    assert result.priority is None
    assert result.recommended_route is None
    assert result.stop.required
    assert "STOP-04" in result.stop.reason_ids
    assert any(question.blocking for question in result.questions)


def test_mx_hc_boundary_question_and_stop_are_policy_driven() -> None:
    incomplete = evaluate(
        complete_evidence(
            impact="high",
            urgency="critical",
            critical_impact_reassessment=None,
        )
    )
    assert incomplete.outcome is TriageOutcome.INCOMPLETE
    assert incomplete.priority is None
    assert "DQ-01" in {question.question_id for question in incomplete.questions}
    assert incomplete.stop.reason_ids == ("STOP-03", "STOP-04")

    complete = evaluate(complete_evidence(impact="high", urgency="critical"))
    assert complete.outcome is TriageOutcome.COMPLETE
    assert complete.rule_id == "MX-HC"
    assert complete.priority is Priority.P2
    assert complete.stop.reason_ids == ("STOP-03",)
    assert complete.recommended_route is SupportRoute.INCIDENT_COORDINATION


def test_mx_cc_stops_uncoordinated_changes() -> None:
    result = evaluate(complete_evidence(impact="critical", urgency="critical"))
    assert result.outcome is TriageOutcome.COMPLETE
    assert result.rule_id == "MX-CC"
    assert result.priority is Priority.P1
    assert result.recommended_route is SupportRoute.INCIDENT_COORDINATION
    assert result.stop.reason_ids == ("STOP-02",)
