"""Fail-closed loading and validation of the versioned triage policy."""

import hashlib
import json
from collections.abc import Iterable
from datetime import date
from itertools import product
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from supportops.domain.priority_matrix import Impact, Priority, Urgency
from supportops.domain.triage import RiskSignal, SupportRoute
from supportops.errors import ConfigurationError

SUPPORTED_SCHEMA_VERSION = "1"
DEFAULT_POLICY_NAME = "triage-v1.json"
EXPECTED_ESCALATIONS = {f"ESC-{number:02d}" for number in range(1, 7)}
EXPECTED_QUESTIONS = {f"DQ-{number:02d}" for number in range(1, 13)}
EXPECTED_STOPS = {f"STOP-{number:02d}" for number in range(1, 8)}
ALLOWED_EVIDENCE_FIELDS = {
    "affected_scope",
    "scope_source",
    "affected_process",
    "process_criticality",
    "workaround_status",
    "workaround_validation",
    "business_consequence",
    "containment_status",
    "critical_impact_reassessment",
    "deadline",
    "deadline_owner",
    "delay_consequence",
    "time_to_harm",
    "condition_stability",
    "failure_frequency",
    "trend",
}


class MatrixRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    impact: Impact
    urgency: Urgency
    priority: Priority
    rationale: str
    baseline_route: SupportRoute
    boundary_required_fields: tuple[str, ...] = Field(default=(), max_length=4)
    boundary_question_ids: tuple[str, ...] = Field(default=(), max_length=4)
    stop_rule_ids: tuple[str, ...] = Field(default=(), max_length=7)


class EscalationRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    destination: SupportRoute
    description: str


class QuestionRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str
    topic: str
    question: str
    required_evidence: str
    reason: str
    blocking: bool


class StopRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    destination: SupportRoute
    description: str


class TriagePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: Literal["supportops-triage"]
    schema_version: str
    matrix_version: str = Field(min_length=1, max_length=100)
    effective_date: date
    fallback_behavior: Literal["fail_closed"]
    allowed_impacts: tuple[Impact, ...]
    allowed_urgencies: tuple[Urgency, ...]
    allowed_priorities: tuple[Priority, ...]
    route_order: tuple[SupportRoute, ...]
    v1_conservative_note: str = Field(min_length=1, max_length=2000)
    impact_required_fields: dict[Impact, tuple[str, ...]]
    urgency_required_fields: dict[Urgency, tuple[str, ...]]
    matrix_rules: tuple[MatrixRule, ...]
    escalation_rules: tuple[EscalationRule, ...]
    conditional_escalation: dict[str, SupportRoute]
    risk_signal_ids: tuple[RiskSignal, ...]
    questions: tuple[QuestionRule, ...]
    stop_rules: tuple[StopRule, ...]
    checksum: str = Field(default="", pattern=r"^$|^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_policy_invariants(self) -> "TriagePolicy":
        if self.schema_version != SUPPORTED_SCHEMA_VERSION:
            raise ValueError("unsupported policy schema")
        if tuple(self.allowed_impacts) != tuple(Impact):
            raise ValueError("impact enum declaration is invalid")
        if tuple(self.allowed_urgencies) != tuple(Urgency):
            raise ValueError("urgency enum declaration is invalid")
        if set(self.allowed_priorities) != set(Priority):
            raise ValueError("priority enum declaration is invalid")
        if self.route_order != (
            SupportRoute.N1,
            SupportRoute.N2,
            SupportRoute.INCIDENT_COORDINATION,
        ):
            raise ValueError("route order is invalid")
        if set(self.impact_required_fields) != set(Impact):
            raise ValueError("impact evidence configuration is incomplete")
        if set(self.urgency_required_fields) != set(Urgency):
            raise ValueError("urgency evidence configuration is incomplete")
        configured_fields = {
            field
            for fields in (
                *self.impact_required_fields.values(),
                *self.urgency_required_fields.values(),
            )
            for field in fields
        }
        if not configured_fields.issubset(ALLOWED_EVIDENCE_FIELDS):
            raise ValueError("policy references an unsupported evidence field")
        self._validate_matrix()
        self._validate_ids(
            (rule.rule_id for rule in self.escalation_rules), EXPECTED_ESCALATIONS
        )
        self._validate_ids(
            (rule.question_id for rule in self.questions), EXPECTED_QUESTIONS
        )
        self._validate_ids((rule.rule_id for rule in self.stop_rules), EXPECTED_STOPS)
        escalation_destinations = {
            rule.rule_id: rule.destination for rule in self.escalation_rules
        }
        if escalation_destinations != {
            "ESC-01": SupportRoute.INCIDENT_COORDINATION,
            "ESC-02": SupportRoute.N2,
            "ESC-03": SupportRoute.INCIDENT_COORDINATION,
            "ESC-04": SupportRoute.N2,
            "ESC-05": SupportRoute.INCIDENT_COORDINATION,
            "ESC-06": SupportRoute.N2,
        }:
            raise ValueError("escalation destinations are invalid")
        stop_destinations = {rule.rule_id: rule.destination for rule in self.stop_rules}
        if stop_destinations != {
            "STOP-01": SupportRoute.INCIDENT_COORDINATION,
            "STOP-02": SupportRoute.N2,
            "STOP-03": SupportRoute.INCIDENT_COORDINATION,
            "STOP-04": SupportRoute.N2,
            "STOP-05": SupportRoute.N2,
            "STOP-06": SupportRoute.N2,
            "STOP-07": SupportRoute.INCIDENT_COORDINATION,
        }:
            raise ValueError("stop destinations are invalid")
        blocking = {rule.question_id: rule.blocking for rule in self.questions}
        if {key for key, value in blocking.items() if value} != {
            "DQ-01",
            "DQ-02",
            "DQ-03",
            "DQ-04",
            "DQ-10",
        }:
            raise ValueError("diagnostic question blocking policy is invalid")
        if set(self.risk_signal_ids) != set(RiskSignal):
            raise ValueError("risk catalog is invalid")
        matrix_boundaries = {
            rule.rule_id: (
                rule.boundary_required_fields,
                rule.boundary_question_ids,
                rule.stop_rule_ids,
            )
            for rule in self.matrix_rules
            if rule.boundary_required_fields
            or rule.boundary_question_ids
            or rule.stop_rule_ids
        }
        if matrix_boundaries != {
            "MX-HC": (
                ("critical_impact_reassessment",),
                ("DQ-01",),
                ("STOP-03",),
            ),
            "MX-CC": ((), (), ("STOP-02",)),
        }:
            raise ValueError("matrix boundary behavior is invalid")
        if self.conditional_escalation != {
            "MX-LH": SupportRoute.N2,
            "MX-MM": SupportRoute.N2,
            "MX-MH": SupportRoute.INCIDENT_COORDINATION,
        }:
            raise ValueError("conditional escalation configuration is invalid")
        return self

    def _validate_matrix(self) -> None:
        expected_pairs = set(product(Impact, Urgency))
        pairs = [(rule.impact, rule.urgency) for rule in self.matrix_rules]
        if len(pairs) != 16 or len(set(pairs)) != 16 or set(pairs) != expected_pairs:
            raise ValueError("matrix must contain exactly one rule per combination")
        rule_ids = [rule.rule_id for rule in self.matrix_rules]
        if len(set(rule_ids)) != 16:
            raise ValueError("matrix rule IDs must be unique")
        labels = {
            Impact.LOW: "L",
            Impact.MODERATE: "M",
            Impact.HIGH: "H",
            Impact.CRITICAL: "C",
            Urgency.LOW: "L",
            Urgency.MODERATE: "M",
            Urgency.HIGH: "H",
            Urgency.CRITICAL: "C",
        }
        for rule in self.matrix_rules:
            expected_id = f"MX-{labels[rule.impact]}{labels[rule.urgency]}"
            if rule.rule_id != expected_id:
                raise ValueError("matrix rule ID does not match its combination")
            if not set(rule.boundary_required_fields).issubset(ALLOWED_EVIDENCE_FIELDS):
                raise ValueError("matrix boundary references unsupported evidence")
            if not set(rule.boundary_question_ids).issubset(EXPECTED_QUESTIONS):
                raise ValueError("matrix boundary references unsupported question")
            if not set(rule.stop_rule_ids).issubset(EXPECTED_STOPS):
                raise ValueError("matrix boundary references unsupported stop rule")
            is_critical_pair = (
                rule.impact is Impact.CRITICAL and rule.urgency is Urgency.CRITICAL
            )
            if (rule.priority is Priority.P1) != is_critical_pair:
                raise ValueError("P1 boundary is contradictory")
            if (
                rule.impact in {Impact.HIGH, Impact.CRITICAL}
                or rule.urgency in {Urgency.HIGH, Urgency.CRITICAL}
            ) and rule.priority in {Priority.P3, Priority.P4}:
                raise ValueError("high or critical dimension violates the P2 floor")

    @staticmethod
    def _validate_ids(values: Iterable[str], expected: set[str]) -> None:
        found = list(values)
        if len(found) != len(set(found)) or set(found) != expected:
            raise ValueError("policy rule collection is incomplete or duplicated")

    def matrix_rule(self, impact: Impact, urgency: Urgency) -> MatrixRule:
        return next(
            rule
            for rule in self.matrix_rules
            if rule.impact is impact and rule.urgency is urgency
        )

    def question(self, question_id: str) -> QuestionRule:
        return next(rule for rule in self.questions if rule.question_id == question_id)

    def route_for_escalation(self, rule_id: str) -> SupportRoute:
        return next(
            rule.destination
            for rule in self.escalation_rules
            if rule.rule_id == rule_id
        )

    def route_for_stop(self, rule_id: str) -> SupportRoute:
        return next(
            rule.destination for rule in self.stop_rules if rule.rule_id == rule_id
        )


def default_policy_path() -> Path:
    return Path(__file__).with_name("policies") / DEFAULT_POLICY_NAME


def load_triage_policy(path: Path | None = None) -> TriagePolicy:
    """Load one policy without fallback and without exposing filesystem details."""

    selected = path or default_policy_path()
    identifier = selected.name or DEFAULT_POLICY_NAME
    try:
        payload_bytes = selected.read_bytes()
        payload = json.loads(payload_bytes.decode("utf-8"))
        checksum = hashlib.sha256(payload_bytes).hexdigest()
        return TriagePolicy.model_validate({**payload, "checksum": checksum})
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError, TypeError):
        raise ConfigurationError(
            f"Invalid triage policy '{identifier}'. Correct the versioned policy "
            "configuration and restart; no fallback was applied."
        ) from None
