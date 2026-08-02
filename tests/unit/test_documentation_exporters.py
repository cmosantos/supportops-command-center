import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from supportops.domain.documentation import (
    DocumentationSections,
    IncidentDocumentation,
    PerformedProcedure,
)
from supportops.exporters import (
    HEADINGS,
    JsonIncidentExporter,
    MarkdownIncidentExporter,
)


def document() -> IncidentDocumentation:
    return IncidentDocumentation(
        id="doc-1",
        incident_id="incident/../../hostile",
        revision=2,
        generated_at=datetime(2026, 8, 2, tzinfo=UTC),
        generated_by="analyst",
        sections=DocumentationSections(
            executive_summary="# injected\n<script>alert(1)</script>",
            technical_description="Descrição técnica",
            collected_evidence=("evidence",),
            evaluated_hypotheses=("No persisted information available.",),
            suggested_procedures=("suggestion only",),
            performed_procedures=("performed fact",),
            applied_solution="solution",
            result_and_preventive_recommendation="result",
            ticket_ready_text="ticket text",
        ),
    )


def test_markdown_has_exact_order_and_inert_hostile_content() -> None:
    artifact = MarkdownIncidentExporter().export(document())
    text = artifact.content.decode()
    assert [line[3:] for line in text.splitlines() if line.startswith("## ")] == [
        heading for heading, _ in HEADINGS
    ]
    assert "\\# injected" in text
    assert "&lt;script&gt;" in text
    assert "/" not in artifact.filename


def test_markdown_literalizes_all_active_constructs() -> None:
    hostile = (
        "[link](javascript:alert(1)) ![img](x) <https://bad>\n"
        "> quote\n- list\n```py\nx\n```\n# heading\n_a_ *b* `c`\x00"
    )
    candidate = document().model_copy(
        update={
            "sections": document().sections.model_copy(
                update={"executive_summary": hostile}
            )
        }
    )
    text = MarkdownIncidentExporter().export(candidate).content.decode()
    assert "[link](" not in text
    assert "![img]" not in text
    assert "<https" not in text
    assert "\n> quote" not in text
    assert "\n- list" not in text
    assert "```" not in text
    assert "\n# heading" not in text
    assert "javascript:alert" in text
    assert "\x00" not in text
    assert len([line for line in text.splitlines() if line.startswith("## ")]) == 9


def test_json_is_strict_deterministic_unicode() -> None:
    exporter = JsonIncidentExporter()
    first = exporter.export(document())
    assert first.content == exporter.export(document()).content
    payload = json.loads(first.content.decode("utf-8"))
    assert payload["schema_version"] == "1"
    assert payload["sections"]["technical_description"] == "Descrição técnica"


def test_output_models_require_nonblank_complete_reference_and_utc() -> None:
    non_utc = datetime(2026, 8, 2, tzinfo=timezone(timedelta(hours=1)))
    with pytest.raises(ValidationError):
        PerformedProcedure(
            id="p",
            incident_id="i",
            sequence=1,
            description=" ",
            result="ok",
            performed_at=non_utc,
            actor_reference="n1",
            suggested_action_id="a",
            suggested_action_version=None,
            suggested_action_digest=None,
        )
    with pytest.raises(ValidationError):
        document().model_copy(update={"generated_at": non_utc}).model_validate(
            {**document().model_dump(), "generated_at": non_utc}
        )


@pytest.mark.parametrize(
    ("action_id", "version", "digest"),
    [
        (" ", 1, "0" * 64),
        ("a", 0, "0" * 64),
        ("a", -1, "0" * 64),
        ("a", 1, "bad"),
        ("a", None, None),
        (None, 1, "0" * 64),
    ],
)
def test_performed_output_rejects_invalid_action_reference(
    action_id: str | None, version: int | None, digest: str | None
) -> None:
    with pytest.raises(ValidationError):
        PerformedProcedure(
            id="p",
            incident_id="i",
            sequence=1,
            description="done",
            result="ok",
            performed_at=datetime(2026, 8, 2, tzinfo=UTC),
            actor_reference="n1",
            suggested_action_id=action_id,
            suggested_action_version=version,
            suggested_action_digest=digest,
        )
