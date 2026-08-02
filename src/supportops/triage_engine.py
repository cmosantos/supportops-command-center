"""Pure deterministic triage evaluation; no persistence or presentation concerns."""

from datetime import datetime

from supportops.domain.priority_matrix import Impact, Urgency
from supportops.domain.triage import (
    DiagnosticQuestion,
    RiskAssessmentStatus,
    StopOutcome,
    SupportRoute,
    TriageEvidence,
    TriageOutcome,
    TriageResult,
)
from supportops.triage_policy import TriagePolicy

ROUTE_RANK = {
    SupportRoute.N1: 1,
    SupportRoute.N2: 2,
    SupportRoute.INCIDENT_COORDINATION: 3,
}
FIELD_QUESTION = {
    "affected_scope": "DQ-01",
    "scope_source": "DQ-01",
    "affected_process": "DQ-02",
    "process_criticality": "DQ-02",
    "business_consequence": "DQ-02",
    "workaround_status": "DQ-03",
    "workaround_validation": "DQ-03",
    "containment_status": "DQ-03",
    "deadline": "DQ-04",
    "deadline_owner": "DQ-04",
    "delay_consequence": "DQ-04",
    "time_to_harm": "DQ-04",
    "condition_stability": "DQ-05",
    "failure_frequency": "DQ-05",
    "trend": "DQ-05",
}


def highest_route(routes: list[SupportRoute]) -> SupportRoute | None:
    return max(routes, key=ROUTE_RANK.__getitem__) if routes else None


def evaluate_triage(
    policy: TriagePolicy,
    evidence: TriageEvidence,
    *,
    incident_id: str,
    snapshot_id: str,
    generated_at: datetime,
    created_by: str | None,
) -> TriageResult:
    """Evaluate the exact supplied facts with the exact policy revision."""

    impact, urgency, dimension_conflicts = _effective_dimensions(policy, evidence)
    effective_evidence = evidence.model_copy(
        update={"impact": impact, "urgency": urgency}
    )
    candidate_rule = (
        policy.matrix_rule(impact, urgency)
        if impact is not None and urgency is not None
        else None
    )
    missing = _missing_evidence(policy, effective_evidence)
    missing.extend(dimension_conflicts)
    boundary_missing: list[str] = []
    if candidate_rule is not None:
        boundary_missing = [
            field
            for field in candidate_rule.boundary_required_fields
            if getattr(effective_evidence, field) is None
        ]
        missing.extend(boundary_missing)
    missing = list(dict.fromkeys(missing))
    question_ids = _question_ids(effective_evidence, missing)
    if candidate_rule is not None and boundary_missing:
        question_ids = sorted(
            set(question_ids).union(candidate_rule.boundary_question_ids)
        )
    questions = tuple(_question(policy, identifier) for identifier in question_ids)
    blocking_question_ids = tuple(
        question.question_id for question in questions if question.blocking
    )
    missing.extend(
        f"blocking_question:{identifier}"
        for identifier in blocking_question_ids
        if f"blocking_question:{identifier}" not in missing
    )
    incomplete = bool(missing or evidence.evidence_conflicts or blocking_question_ids)
    escalation_reasons = _escalation_reasons(
        effective_evidence, None if incomplete else policy
    )
    stop_reasons = _stop_reasons(effective_evidence, incomplete)
    if candidate_rule is not None:
        stop_reasons.extend(
            rule_id
            for rule_id in candidate_rule.stop_rule_ids
            if rule_id not in stop_reasons
        )
    stop_reasons.sort()
    stop_route = highest_route(
        [policy.route_for_stop(reason) for reason in stop_reasons]
    )

    normalized = evidence.model_dump(mode="json")
    if incomplete:
        return TriageResult(
            snapshot_id=snapshot_id,
            incident_id=incident_id,
            outcome=TriageOutcome.INCOMPLETE,
            policy_id=policy.policy_id,
            schema_version=policy.schema_version,
            matrix_version=policy.matrix_version,
            policy_checksum=policy.checksum,
            normalized_input=normalized,
            rule_id=None,
            rationale=None,
            impact=impact,
            urgency=urgency,
            priority=None,
            recommended_route=None,
            escalation_required=bool(escalation_reasons or stop_reasons),
            escalation_reason_ids=tuple(escalation_reasons),
            missing_evidence=tuple(missing),
            questions=questions,
            stop=StopOutcome(
                required=bool(stop_reasons),
                reason_ids=tuple(stop_reasons),
                recommended_route=stop_route,
            ),
            generated_at=generated_at,
            created_by=created_by,
        )

    if impact is None or urgency is None:
        raise RuntimeError("complete evaluation lost required dimensions")
    rule = candidate_rule or policy.matrix_rule(impact, urgency)
    escalation_reasons = _escalation_reasons(effective_evidence, policy)
    routes = [rule.baseline_route]
    routes.extend(policy.route_for_escalation(reason) for reason in escalation_reasons)
    if (
        effective_evidence.conditional_triggers
        and rule.rule_id in policy.conditional_escalation
    ):
        routes.append(policy.conditional_escalation[rule.rule_id])
        escalation_reasons.extend(
            f"COND-{rule.rule_id}-{trigger.value}"
            for trigger in effective_evidence.conditional_triggers
        )
    if rule.baseline_route is SupportRoute.N1 and not _all_n1_conditions(
        effective_evidence
    ):
        routes.append(SupportRoute.N2)
    if stop_route is not None:
        routes.append(stop_route)
    recommended = highest_route(routes)
    return TriageResult(
        snapshot_id=snapshot_id,
        incident_id=incident_id,
        outcome=TriageOutcome.COMPLETE,
        policy_id=policy.policy_id,
        schema_version=policy.schema_version,
        matrix_version=policy.matrix_version,
        policy_checksum=policy.checksum,
        normalized_input=normalized,
        rule_id=rule.rule_id,
        rationale=rule.rationale,
        impact=impact,
        urgency=urgency,
        priority=rule.priority,
        recommended_route=recommended,
        escalation_required=bool(escalation_reasons or stop_reasons),
        escalation_reason_ids=tuple(escalation_reasons),
        missing_evidence=(),
        questions=questions,
        stop=StopOutcome(
            required=bool(stop_reasons),
            reason_ids=tuple(stop_reasons),
            recommended_route=stop_route,
        ),
        generated_at=generated_at,
        created_by=created_by,
    )


def _effective_dimensions(
    policy: TriagePolicy, evidence: TriageEvidence
) -> tuple[Impact | None, Urgency | None, list[str]]:
    impact = (
        max(
            evidence.supported_impact_criteria,
            key=policy.allowed_impacts.index,
        )
        if evidence.supported_impact_criteria
        else None
    )
    urgency = (
        max(
            evidence.supported_urgency_criteria,
            key=policy.allowed_urgencies.index,
        )
        if evidence.supported_urgency_criteria
        else None
    )
    conflicts: list[str] = []
    if (
        evidence.impact is not None
        and impact is not None
        and evidence.impact is not impact
    ):
        conflicts.append("contradiction:impact")
    if (
        evidence.urgency is not None
        and urgency is not None
        and evidence.urgency is not urgency
    ):
        conflicts.append("contradiction:urgency")
    return impact, urgency, conflicts


def _missing_evidence(policy: TriagePolicy, evidence: TriageEvidence) -> list[str]:
    missing: list[str] = []
    if not evidence.supported_impact_criteria or evidence.impact is None:
        missing.append("supported_impact_criteria")
    else:
        missing.extend(
            field
            for field in policy.impact_required_fields[evidence.impact]
            if getattr(evidence, field) is None
        )
    if not evidence.supported_urgency_criteria or evidence.urgency is None:
        missing.append("supported_urgency_criteria")
    else:
        missing.extend(
            field
            for field in policy.urgency_required_fields[evidence.urgency]
            if getattr(evidence, field) is None
        )
    if evidence.risk_assessment_status is RiskAssessmentStatus.NOT_ASSESSED:
        missing.append("risk_assessment_status")
    for conflict in evidence.evidence_conflicts:
        missing.append(f"contradiction:{conflict}")
    return list(dict.fromkeys(missing))


def _question_ids(evidence: TriageEvidence, missing: list[str]) -> list[str]:
    identifiers: set[str] = set()
    if any(
        item in missing
        for item in (
            "supported_impact_criteria",
            "contradiction:impact",
            "affected_scope",
            "scope_source",
        )
    ):
        identifiers.add("DQ-01")
    if (
        "affected_process" in missing
        or "business_consequence" in missing
        or evidence.process_criticality is None
    ):
        identifiers.add("DQ-02")
    for field in missing:
        identifier = FIELD_QUESTION.get(field)
        if identifier:
            identifiers.add(identifier)
    if "supported_urgency_criteria" in missing or "contradiction:urgency" in missing:
        identifiers.add("DQ-04")
    if evidence.time_to_harm is None or (
        evidence.condition_stability is None and evidence.failure_frequency is None
    ):
        identifiers.add("DQ-05")
    if evidence.symptom_context is None:
        identifiers.add("DQ-06")
    if evidence.prior_actions is None:
        identifiers.add("DQ-07")
    if evidence.recent_change is None or evidence.cause_materially_uncertain:
        identifiers.add("DQ-08")
    if evidence.corroboration is None and (
        evidence.impact in {Impact.HIGH, Impact.CRITICAL}
        or evidence.multi_user_or_scope_suspected
        or evidence.cross_team_or_vendor
    ):
        identifiers.add("DQ-09")
    if (
        evidence.urgency in {Urgency.HIGH, Urgency.CRITICAL}
        and evidence.workaround_validation is None
    ):
        identifiers.add("DQ-03")
    if evidence.risk_assessment_status is RiskAssessmentStatus.NOT_ASSESSED:
        identifiers.add("DQ-10")
    if evidence.requires_admin_or_change is None:
        identifiers.add("DQ-11")
    if (
        evidence.controlled_test_considered
        and evidence.safe_reproduction_criteria is None
    ):
        identifiers.add("DQ-12")
    if evidence.evidence_conflicts:
        identifiers.update(("DQ-01", "DQ-04"))
    return sorted(identifiers)


def _question(policy: TriagePolicy, identifier: str) -> DiagnosticQuestion:
    rule = policy.question(identifier)
    return DiagnosticQuestion.model_validate(rule.model_dump())


def _escalation_reasons(
    evidence: TriageEvidence, policy: TriagePolicy | None
) -> list[str]:
    reasons: list[str] = []
    priority_p1 = False
    if (
        policy is not None
        and evidence.impact is not None
        and evidence.urgency is not None
    ):
        priority_p1 = (
            policy.matrix_rule(evidence.impact, evidence.urgency).priority.value == "P1"
        )
    if priority_p1:
        reasons.append("ESC-01")
    if (
        evidence.impact in {Impact.HIGH, Impact.CRITICAL}
        or evidence.urgency is Urgency.CRITICAL
    ):
        reasons.append("ESC-02")
    if evidence.risk_assessment_status in {
        RiskAssessmentStatus.SUSPECTED,
        RiskAssessmentStatus.CONFIRMED,
    }:
        reasons.append("ESC-03")
    if evidence.requires_admin_or_change:
        reasons.append("ESC-04")
    if evidence.cross_team_or_vendor:
        reasons.append("ESC-05")
    if (
        evidence.n1_checks_exhausted
        or evidence.evidence_conflicts
        or evidence.cause_materially_uncertain
        or evidence.recurring_after_fix
    ):
        reasons.append("ESC-06")
    return reasons


def _stop_reasons(evidence: TriageEvidence, incomplete: bool) -> list[str]:
    reasons: list[str] = []
    if evidence.risk_assessment_status in {
        RiskAssessmentStatus.SUSPECTED,
        RiskAssessmentStatus.CONFIRMED,
    }:
        reasons.append("STOP-01")
    if any(
        (
            evidence.next_step_destructive,
            evidence.next_step_administrative,
            evidence.next_step_configuration_change,
            evidence.next_step_outside_runbook,
            evidence.required_approval_missing,
        )
    ):
        reasons.append("STOP-02")
    if evidence.scope_increasing or evidence.urgency_increasing:
        reasons.append("STOP-03")
    if incomplete or evidence.evidence_conflicts:
        reasons.append("STOP-04")
    if evidence.controlled_attempts >= 2 or evidence.retry_compounds_impact:
        reasons.append("STOP-05")
    if evidence.ownership_or_recovery_unknown:
        reasons.append("STOP-06")
    if evidence.cross_team_or_vendor or evidence.major_incident_procedure:
        reasons.append("STOP-07")
    return reasons


def _all_n1_conditions(evidence: TriageEvidence) -> bool:
    sufficiently_known = all(
        (
            evidence.affected_scope,
            evidence.time_to_harm,
            evidence.symptom_context,
            evidence.prior_actions,
        )
    )
    return bool(
        sufficiently_known
        and evidence.within_approved_runbook_or_noninvasive
        and evidence.n1_safe_boundary
        and not evidence.requires_admin_or_change
        and evidence.expected_result_defined
        and evidence.stop_condition_defined
    )
