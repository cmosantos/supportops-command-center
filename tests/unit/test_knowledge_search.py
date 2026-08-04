import json
from pathlib import Path

import pytest

from supportops.domain.knowledge import KnowledgeDocument
from supportops.errors import InputValidationError, KnowledgeError, NotFoundError
from supportops.knowledge_search import (
    MarkdownKnowledgeSearch,
    normalize_text,
    query_terms,
)


def canonical_body(objective: str = "Collect network evidence safely.") -> str:
    return f"""# Objective

{objective}

## Safe evidence

- Record evidence without sensitive data.

## Non-executable guidance

Route the action to the authorized team.

## Stop and escalate

Stop when there is risk or a need for administrative privilege.
"""


def write_runbook(
    root: Path,
    *,
    document_id: str = "sample-runbook",
    title: str = "Network unavailable",
    aliases: str = '["no internet"]',
    symptoms: str = '["connection down"]',
    keywords: str = '["wifi"]',
    body: str | None = None,
    filename: str = "sample.md",
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / filename
    body = canonical_body() if body is None else body
    path.write_text(
        f'''+++
id = "{document_id}"
title = "{title}"
aliases = {aliases}
category = "Connectivity"
symptoms = {symptoms}
keywords = {keywords}
risk_notes = ["do not run commands"]
escalation_criteria = ["widespread impact"]
revision = "1.0.0"
+++
{body}
''',
        encoding="utf-8",
    )
    return path


def test_normalization_is_case_and_accent_insensitive() -> None:
    assert normalize_text("RÉSUMÉ, User!") == "resume user"
    assert query_terms("Network network WI-FI") == ("fi", "network", "wi")


@pytest.mark.parametrize(
    ("query", "score"),
    [
        ("unavailable", 50),
        ("internet", 40),
        ("down", 30),
        ("wifi", 25),
        ("evidence", 10),
    ],
)
def test_each_searchable_field_contributes_weight(
    tmp_path: Path, query: str, score: int
) -> None:
    write_runbook(tmp_path)
    result = MarkdownKnowledgeSearch(tmp_path).search(query)[0]
    assert result.score == score
    assert result.matched_terms == (normalize_text(query),)


def test_duplicate_query_terms_count_once(tmp_path: Path) -> None:
    write_runbook(
        tmp_path,
        title="Network",
        aliases='["network"]',
        symptoms='["network"]',
        keywords='["network"]',
        body=canonical_body("Network"),
    )
    result = MarkdownKnowledgeSearch(tmp_path).search("NETWORK network nétwork")[0]
    assert result.score == 155
    assert result.matched_terms == ("network",)


def test_ranking_tie_break_and_json_are_repeatable(tmp_path: Path) -> None:
    write_runbook(tmp_path, document_id="zeta", title="Beta network", filename="z.md")
    write_runbook(tmp_path, document_id="alpha", title="Álpha network", filename="a.md")
    adapter = MarkdownKnowledgeSearch(tmp_path)
    first = adapter.search("network")
    second = adapter.search("NÉTWORK")
    assert [item.id for item in first] == ["alpha", "zeta"]
    assert json.dumps(
        [item.model_dump() for item in first], sort_keys=True
    ) == json.dumps([item.model_dump() for item in second], sort_keys=True)


def test_no_result_is_empty(tmp_path: Path) -> None:
    write_runbook(tmp_path)
    assert MarkdownKnowledgeSearch(tmp_path).search("missing") == ()


def test_excerpt_omits_markdown_heading(tmp_path: Path) -> None:
    write_runbook(tmp_path, body=canonical_body("Collect safe evidence."))
    result = MarkdownKnowledgeSearch(tmp_path).search("internet")[0]
    assert result.excerpt == "Collect safe evidence."


@pytest.mark.parametrize("query", ["", "   ", "!!!", "\u0301"])
def test_invalid_query_is_rejected(tmp_path: Path, query: str) -> None:
    write_runbook(tmp_path)
    with pytest.raises(InputValidationError):
        MarkdownKnowledgeSearch(tmp_path).search(query)


def test_get_rejects_traversal_and_absolute_paths(tmp_path: Path) -> None:
    write_runbook(tmp_path)
    adapter = MarkdownKnowledgeSearch(tmp_path)
    for unsafe in ("../sample", "..\\sample", "/sample", "C:\\sample"):
        with pytest.raises(InputValidationError):
            adapter.get(unsafe)


def test_get_and_health_use_typed_document(tmp_path: Path) -> None:
    write_runbook(tmp_path)
    adapter = MarkdownKnowledgeSearch(tmp_path)
    assert adapter.health() is True
    assert isinstance(adapter.get("sample-runbook"), KnowledgeDocument)
    with pytest.raises(NotFoundError):
        adapter.get("missing")


@pytest.mark.parametrize(
    "invalid",
    ["plain markdown", "+++\nid = 'bad'\n+++\n", "+++\ninvalid = [\n+++\nbody"],
)
def test_invalid_content_fails_closed(tmp_path: Path, invalid: str) -> None:
    write_runbook(tmp_path)
    (tmp_path / "invalid.md").write_text(invalid, encoding="utf-8")
    with pytest.raises(KnowledgeError, match="invalid runbook"):
        MarkdownKnowledgeSearch(tmp_path).search("network")


@pytest.mark.parametrize(
    "body",
    [
        canonical_body().replace(
            "## Safe evidence\n\n- Record evidence without sensitive data.\n\n",
            "",
        ),
        canonical_body().replace(
            "## Safe evidence\n\n- Record evidence without sensitive data.",
            "## Safe evidence",
        ),
        canonical_body() + "\n## Stop and escalate\n\nDuplicate.",
        "# Objective\n## Safe evidence\n"
        "## Non-executable guidance\n## Stop and escalate",
    ],
    ids=("missing", "empty", "duplicate", "headings-only"),
)
def test_invalid_canonical_sections_fail_closed(tmp_path: Path, body: str) -> None:
    write_runbook(tmp_path, body=body)
    with pytest.raises(KnowledgeError, match="invalid runbook"):
        MarkdownKnowledgeSearch(tmp_path).health()


@pytest.mark.parametrize("operation", ["health", "search", "get"])
def test_empty_corpus_fails_closed(tmp_path: Path, operation: str) -> None:
    adapter = MarkdownKnowledgeSearch(tmp_path)
    with pytest.raises(KnowledgeError, match="no valid runbooks"):
        if operation == "health":
            adapter.health()
        elif operation == "search":
            adapter.search("network")
        else:
            adapter.get("sample-runbook")


def test_duplicate_ids_fail_closed(tmp_path: Path) -> None:
    write_runbook(tmp_path, filename="one.md")
    write_runbook(tmp_path, filename="two.md")
    with pytest.raises(KnowledgeError, match="duplicate"):
        MarkdownKnowledgeSearch(tmp_path).health()


def test_unsupported_encoding_is_safe(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe")
    with pytest.raises(KnowledgeError, match="encoding"):
        MarkdownKnowledgeSearch(tmp_path).health()


def test_missing_root_error_does_not_disclose_path(tmp_path: Path) -> None:
    root = tmp_path / "secret-location"
    with pytest.raises(KnowledgeError) as caught:
        MarkdownKnowledgeSearch(root).health()
    assert str(root) not in caught.value.public_message


def test_hostile_content_is_inert_data(tmp_path: Path) -> None:
    write_runbook(
        tmp_path,
        body=canonical_body("$(whoami) {{ import }}; rm -rf / network"),
    )
    result = MarkdownKnowledgeSearch(tmp_path).search("whoami")[0]
    assert "whoami" in result.excerpt
