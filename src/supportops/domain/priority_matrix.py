"""Structural priority-matrix contract without classification behavior."""

from enum import StrEnum
from itertools import product

from pydantic import BaseModel, ConfigDict, model_validator


class Impact(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Urgency(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class PriorityMatrixRule(BaseModel):
    """One structurally valid impact/urgency cell."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    impact: Impact
    urgency: Urgency
    priority: Priority


class PriorityMatrixConfiguration(BaseModel):
    """A complete 4x4 matrix definition, deliberately without lookup methods."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    matrix_version: str
    rules: tuple[PriorityMatrixRule, ...]

    @model_validator(mode="after")
    def validate_complete_unique_matrix(self) -> "PriorityMatrixConfiguration":
        expected = set(product(Impact, Urgency))
        provided = [(rule.impact, rule.urgency) for rule in self.rules]
        provided_set = set(provided)

        if len(provided) != len(provided_set):
            raise ValueError("matrix contains conflicting duplicate combinations")
        if provided_set != expected:
            missing = len(expected - provided_set)
            unexpected = len(provided_set - expected)
            raise ValueError(
                "matrix must define each impact/urgency combination exactly once "
                f"(missing={missing}, unexpected={unexpected})"
            )
        return self


def structural_matrix_sample() -> PriorityMatrixConfiguration:
    """Build a neutral specimen used only to exercise the structural contract."""

    rules = tuple(
        PriorityMatrixRule(impact=impact, urgency=urgency, priority=Priority.P4)
        for impact, urgency in product(Impact, Urgency)
    )
    return PriorityMatrixConfiguration(
        schema_version="1",
        matrix_version="structural-check-only",
        rules=rules,
    )
