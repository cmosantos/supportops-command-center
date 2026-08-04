import json

import pytest

from supportops.cli import main


def test_human_search_shows_ranking_and_evidence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["knowledge", "search", "OneDrive synchronization"]) == 0
    output = capsys.readouterr().out
    assert "Knowledge matches:" in output
    assert "score:" in output
    assert "matched:" in output
    assert "revision: 1.0.0" in output
    assert "source: onedrive-not-syncing.md" in output
    assert "evidence:" in output


def test_json_search_is_structured(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["knowledge", "search", "account locked", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["results"][0]["id"] == "identity-user-locked"
    assert payload["results"][0]["score"] > 0
    assert payload["results"][0]["matched_terms"]


def test_no_results_human_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["knowledge", "search", "missing-term"]) == 0
    assert capsys.readouterr().out.strip() == "No knowledge matches found."
    assert main(["knowledge", "search", "missing-term", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["results"] == []


def test_invalid_query_uses_safe_error_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["knowledge", "search", "!!!"]) == 2
    output = capsys.readouterr().out
    assert "searchable text" in output
    assert "Traceback" not in output
