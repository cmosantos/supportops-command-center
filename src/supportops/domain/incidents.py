"""Incident lifecycle domain models for the OPEN/CLOSED state machine."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from supportops.domain.priority_matrix import Impact, Urgency


class IncidentStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ApprovalDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class IncidentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    affected_party: str = Field(min_length=1, max_length=200)
    affected_service: str = Field(min_length=1, max_length=200)
    impact: Impact
    urgency: Urgency
    symptoms: str = Field(min_length=1, max_length=10000)
    error_messages: tuple[str, ...] = ()
    actions_already_taken: tuple[str, ...] = ()
    actor_reference: str | None = Field(default=None, max_length=200)

    @field_validator(
        "title", "description", "affected_party", "affected_service", "symptoms"
    )
    @classmethod
    def non_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be blank")
        return normalized


class IncidentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    affected_party: str | None = Field(default=None, min_length=1, max_length=200)
    affected_service: str | None = Field(default=None, min_length=1, max_length=200)
    symptoms: str | None = Field(default=None, min_length=1, max_length=10000)

    @field_validator(
        "title", "description", "affected_party", "affected_service", "symptoms"
    )
    @classmethod
    def optional_non_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be blank")
        return normalized

    def changes(self) -> dict[str, str]:
        return {
            key: value
            for key, value in self.model_dump(exclude={"expected_version"}).items()
            if value is not None
        }


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title: str
    description: str
    affected_party: str
    affected_service: str
    impact: Impact
    urgency: Urgency
    symptoms: str
    error_messages: tuple[str, ...]
    actions_already_taken: tuple[str, ...]
    status: IncidentStatus
    version: int
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    deleted_at: datetime | None
    deletion_reason: str | None
    deletion_confirmed: bool
    pre_deletion_status: IncidentStatus | None
    created_by: str | None

    @property
    def handling_seconds(self) -> float | None:
        if self.closed_at is None:
            return None
        return (self.closed_at - self.created_at).total_seconds()


class IncidentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    incident_id: str
    sequence: int | None = Field(default=None, gt=0)
    event_type: str
    previous_status: IncidentStatus | None
    new_status: IncidentStatus | None
    occurred_at: datetime
    actor_reference: str | None
    details: dict[str, Any]


class ApprovalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1, max_length=200)
    action_version: int = Field(ge=1)
    action_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    action_snapshot: dict[str, Any]
    decision: ApprovalDecision
    approver_reference: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=2000)


class HumanApproval(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    incident_id: str
    action_id: str
    action_version: int
    action_digest: str
    action_snapshot: dict[str, Any]
    decision: ApprovalDecision
    approver_reference: str
    decided_at: datetime
    note: str | None
    created_at: datetime
