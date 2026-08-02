"""Immutable performed-work and incident-documentation models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ExportFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"


class PerformedProcedureInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=10000)
    result: str = Field(min_length=1, max_length=10000)
    actor_reference: str = Field(min_length=1, max_length=200)
    suggested_action_id: str | None = Field(default=None, min_length=1, max_length=200)
    suggested_action_version: int | None = Field(default=None, ge=1)
    suggested_action_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @field_validator("description", "result", "actor_reference")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field must not be blank")
        return value

    @model_validator(mode="after")
    def complete_action_reference(self) -> "PerformedProcedureInput":
        values = (
            self.suggested_action_id,
            self.suggested_action_version,
            self.suggested_action_digest,
        )
        if any(value is not None for value in values) and any(
            value is None for value in values
        ):
            raise ValueError("suggested action reference must be complete")
        return self


class PerformedProcedure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    incident_id: str
    sequence: int = Field(gt=0)
    description: str
    result: str
    performed_at: datetime
    actor_reference: str
    suggested_action_id: str | None = Field(default=None, min_length=1, max_length=200)
    suggested_action_version: int | None = Field(default=None, ge=1)
    suggested_action_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @field_validator("id", "incident_id", "description", "result", "actor_reference")
    @classmethod
    def non_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must not be blank")
        return value

    @model_validator(mode="after")
    def complete_action_reference(self) -> "PerformedProcedure":
        values = (
            self.suggested_action_id,
            self.suggested_action_version,
            self.suggested_action_digest,
        )
        if any(value is not None for value in values) and any(
            value is None for value in values
        ):
            raise ValueError("suggested action reference must be complete")
        return self

    @field_validator("suggested_action_id")
    @classmethod
    def optional_non_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("suggested action ID must not be blank")
        return value

    @field_validator("performed_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        offset = value.utcoffset()
        if value.tzinfo is None or offset is None or offset.total_seconds() != 0:
            raise ValueError("performed_at must be UTC")
        return value


class DocumentationSections(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    executive_summary: str
    technical_description: str
    collected_evidence: tuple[str, ...]
    evaluated_hypotheses: tuple[str, ...]
    suggested_procedures: tuple[str, ...]
    performed_procedures: tuple[str, ...]
    applied_solution: str
    result_and_preventive_recommendation: str
    ticket_ready_text: str

    @model_validator(mode="after")
    def non_empty_sections(self) -> "DocumentationSections":
        for value in self.model_dump().values():
            entries = value if isinstance(value, tuple) else (value,)
            if not entries or any(not str(entry).strip() for entry in entries):
                raise ValueError("documentation sections must not be empty")
        return self


class IncidentDocumentation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    incident_id: str
    revision: int = Field(gt=0)
    generated_at: datetime
    generated_by: str
    sections: DocumentationSections

    @field_validator("id", "incident_id", "generated_by")
    @classmethod
    def non_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must not be blank")
        return value

    @field_validator("generated_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        offset = value.utcoffset()
        if value.tzinfo is None or offset is None or offset.total_seconds() != 0:
            raise ValueError("generated_at must be UTC")
        return value


class ExportArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    incident_id: str
    revision: int
    format: ExportFormat
    media_type: str
    filename: str
    content: bytes


class WrittenExport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    incident_id: str
    revision: int
    format: ExportFormat
    media_type: str
    filename: str
    relative_path: str
