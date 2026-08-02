"""Typed deterministic triage inputs and immutable outcomes."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from supportops.domain.priority_matrix import Impact, Priority, Urgency

EvidenceText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]


class SupportRoute(StrEnum):
    N1 = "N1"
    N2 = "N2"
    INCIDENT_COORDINATION = "incident_coordination"


class TriageOutcome(StrEnum):
    COMPLETE = "triage_complete"
    INCOMPLETE = "triage_incomplete"


class RiskAssessmentStatus(StrEnum):
    NOT_ASSESSED = "not_assessed"
    NONE_IDENTIFIED = "none_identified"
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"


class RiskSignal(StrEnum):
    SECURITY_COMPROMISE = "security_compromise"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    SAFETY_HAZARD = "safety_hazard"
    PRIVACY_EXPOSURE = "privacy_exposure"
    REGULATORY_EXPOSURE = "regulatory_exposure"
    DATA_INTEGRITY_LOSS = "data_integrity_loss"


class ConditionalEscalationTrigger(StrEnum):
    BASELINE_LIMIT_REACHED = "baseline_limit_reached"
    WORKAROUND_FAILED_OR_RISK_INCREASED = "workaround_failed_or_risk_increased"
    LOGS_INACCESSIBLE = "logs_inaccessible"
    RUNBOOK_UNAVAILABLE = "runbook_unavailable"


class TriageEvidence(BaseModel):
    """Structured facts supplied by a human; free text never implies risk."""

    model_config = ConfigDict(extra="forbid")

    impact: Impact | None = None
    urgency: Urgency | None = None
    supported_impact_criteria: tuple[Impact, ...] = Field(default=(), max_length=4)
    supported_urgency_criteria: tuple[Urgency, ...] = Field(default=(), max_length=4)
    affected_scope: EvidenceText | None = None
    scope_source: EvidenceText | None = None
    affected_process: EvidenceText | None = None
    process_criticality: EvidenceText | None = None
    workaround_status: EvidenceText | None = None
    workaround_validation: EvidenceText | None = None
    business_consequence: EvidenceText | None = None
    containment_status: EvidenceText | None = None
    critical_impact_reassessment: EvidenceText | None = None
    deadline: EvidenceText | None = None
    deadline_owner: EvidenceText | None = None
    delay_consequence: EvidenceText | None = None
    time_to_harm: EvidenceText | None = None
    condition_stability: EvidenceText | None = None
    failure_frequency: EvidenceText | None = None
    trend: EvidenceText | None = None
    symptom_context: EvidenceText | None = None
    prior_actions: EvidenceText | None = None
    recent_change: EvidenceText | None = None
    corroboration: EvidenceText | None = None
    risk_assessment_status: RiskAssessmentStatus = RiskAssessmentStatus.NOT_ASSESSED
    risk_signal_ids: tuple[RiskSignal, ...] = Field(default=(), max_length=6)
    requires_admin_or_change: bool | None = None
    cross_team_or_vendor: bool = False
    multi_user_or_scope_suspected: bool = False
    n1_checks_exhausted: bool = False
    cause_materially_uncertain: bool = False
    recurring_after_fix: bool = False
    conditional_triggers: tuple[ConditionalEscalationTrigger, ...] = Field(
        default=(), max_length=4
    )
    within_approved_runbook_or_noninvasive: bool = False
    n1_safe_boundary: bool = False
    expected_result_defined: bool = False
    stop_condition_defined: bool = False
    controlled_test_considered: bool = False
    safe_reproduction_criteria: EvidenceText | None = None
    evidence_conflicts: tuple[EvidenceText, ...] = Field(default=(), max_length=20)
    next_step_destructive: bool = False
    next_step_administrative: bool = False
    next_step_configuration_change: bool = False
    next_step_outside_runbook: bool = False
    required_approval_missing: bool = False
    scope_increasing: bool = False
    urgency_increasing: bool = False
    controlled_attempts: int = Field(default=0, ge=0, le=100)
    retry_compounds_impact: bool = False
    ownership_or_recovery_unknown: bool = False
    major_incident_procedure: bool = False

    @model_validator(mode="after")
    def validate_structured_risk(self) -> "TriageEvidence":
        unique = set(self.risk_signal_ids)
        if len(unique) != len(self.risk_signal_ids):
            raise ValueError("risk signal IDs must be unique")
        if len(set(self.conditional_triggers)) != len(self.conditional_triggers):
            raise ValueError("conditional escalation triggers must be unique")
        if len(set(self.supported_impact_criteria)) != len(
            self.supported_impact_criteria
        ):
            raise ValueError("supported impact criteria must be unique")
        if len(set(self.supported_urgency_criteria)) != len(
            self.supported_urgency_criteria
        ):
            raise ValueError("supported urgency criteria must be unique")
        if (
            self.risk_assessment_status
            in {
                RiskAssessmentStatus.NOT_ASSESSED,
                RiskAssessmentStatus.NONE_IDENTIFIED,
            }
            and self.risk_signal_ids
        ):
            raise ValueError("the selected risk status requires no signal IDs")
        if (
            self.risk_assessment_status
            in {
                RiskAssessmentStatus.SUSPECTED,
                RiskAssessmentStatus.CONFIRMED,
            }
            and not self.risk_signal_ids
        ):
            raise ValueError("suspected or confirmed risk requires a signal ID")
        return self


class DiagnosticQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str
    topic: str
    question: str
    required_evidence: str
    reason: str
    blocking: bool


class StopOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    required: bool
    reason_ids: tuple[str, ...]
    recommended_route: SupportRoute | None


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str
    incident_id: str
    sequence: int | None = Field(default=None, gt=0)
    outcome: TriageOutcome
    policy_id: str
    schema_version: str
    matrix_version: str
    policy_checksum: str
    normalized_input: dict[str, Any]
    rule_id: str | None
    rationale: str | None
    impact: Impact | None
    urgency: Urgency | None
    priority: Priority | None
    recommended_route: SupportRoute | None
    escalation_required: bool
    escalation_reason_ids: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    questions: tuple[DiagnosticQuestion, ...]
    stop: StopOutcome
    generated_at: datetime
    created_by: str | None

    @model_validator(mode="after")
    def validate_outcome_fields(self) -> "TriageResult":
        complete_values = (
            self.rule_id,
            self.rationale,
            self.impact,
            self.urgency,
            self.priority,
            self.recommended_route,
        )
        if self.outcome is TriageOutcome.COMPLETE and any(
            value is None for value in complete_values
        ):
            raise ValueError("complete triage requires all classification fields")
        if self.outcome is TriageOutcome.INCOMPLETE and any(
            value is not None
            for value in (
                self.rule_id,
                self.rationale,
                self.priority,
                self.recommended_route,
            )
        ):
            raise ValueError("incomplete triage cannot fabricate classification")
        return self
