import json
from pathlib import Path

import pytest

from supportops.cli import main
from supportops.config import get_settings


def test_cli_persisted_documentation_journey(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("SUPPORTOPS_DB_PATH", str(tmp_path / "db.sqlite"))
    monkeypatch.setenv("SUPPORTOPS_EXPORT_ROOT", str(tmp_path / "exports"))
    get_settings.cache_clear()
    assert main(["db", "init"]) == 0
    assert (
        main(
            [
                "incident",
                "create",
                "--title",
                "Network",
                "--description",
                "No access",
                "--affected-party",
                "Finance",
                "--affected-service",
                "LAN",
                "--impact",
                "moderate",
                "--urgency",
                "high",
                "--symptoms",
                "Timeout",
            ]
        )
        == 0
    )
    incident_id = json.loads(capsys.readouterr().out.splitlines()[-1])["id"]
    assert (
        main(
            [
                "performed",
                "record",
                incident_id,
                "--description",
                "Checked cable",
                "--result",
                "Cable replaced",
                "--actor",
                "n1",
                "--format",
                "human",
            ]
        )
        == 0
    )
    performed_human = capsys.readouterr().out
    assert all(
        value in performed_human
        for value in (
            "id=",
            f"incident={incident_id}",
            "performed_at:",
            "suggestion_reference:",
        )
    )
    assert (
        main(["document", "generate", incident_id, "--actor", "n1", "--format", "json"])
        == 0
    )
    document = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert document["revision"] == 1
    assert len(document["sections"]) == 9
    assert main(["document", "show", incident_id]) == 0
    human_document = capsys.readouterr().out
    assert all(
        value in human_document
        for value in ("document=", "generated_at=", "generated_by=")
    )
    assert (
        main(["export", incident_id, "--format", "markdown", "--output", "json"]) == 0
    )
    markdown_export = json.loads(capsys.readouterr().out.splitlines()[-1])
    markdown_text = (tmp_path / "exports" / markdown_export["relative_path"]).read_text(
        encoding="utf-8"
    )
    assert (
        len([line for line in markdown_text.splitlines() if line.startswith("## ")])
        == 9
    )
    assert main(["export", incident_id, "--format", "json", "--output", "json"]) == 0
    exported = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert Path(exported["relative_path"]).name == exported["relative_path"]
    assert json.loads(
        (tmp_path / "exports" / exported["relative_path"]).read_text(encoding="utf-8")
    )
