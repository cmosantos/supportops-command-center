import json
from pathlib import Path

import pytest

from supportops.cli import main
from supportops.config import get_settings


def configure_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    path = tmp_path / "cli.db"
    monkeypatch.setenv("SUPPORTOPS_DB_PATH", str(path))
    get_settings.cache_clear()
    return path


def test_cli_database_and_incident_lifecycle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = configure_db(monkeypatch, tmp_path)
    assert main(["db", "status"]) == 0
    assert not path.exists()
    assert main(["db", "init"]) == 0
    assert main(["db", "init"]) == 0
    assert (
        main(
            [
                "incident",
                "create",
                "--title",
                "Printer",
                "--description",
                "Offline",
                "--affected-party",
                "Sales",
                "--affected-service",
                "Printing",
                "--impact",
                "low",
                "--urgency",
                "moderate",
                "--symptoms",
                "No output",
            ]
        )
        == 0
    )
    lines = capsys.readouterr().out.strip().splitlines()
    created = json.loads(lines[-1])
    incident_id = created["id"]
    assert created["status"] == "OPEN"
    assert main(["incident", "close", incident_id]) == 0
    assert main(["incident", "reopen", incident_id]) == 0
    assert main(["incident", "history", incident_id]) == 0
    assert (
        main(["incident", "delete", incident_id, "--reason", "duplicate", "--confirm"])
        == 0
    )
    assert main(["incident", "get", incident_id]) == 4


def test_cli_invalid_input_is_safe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_db(monkeypatch, tmp_path)
    assert main(["db", "init"]) == 0
    assert (
        main(
            [
                "incident",
                "create",
                "--title",
                " ",
                "--description",
                "x",
                "--affected-party",
                "x",
                "--affected-service",
                "x",
                "--impact",
                "bad",
                "--urgency",
                "low",
                "--symptoms",
                "x",
            ]
        )
        == 2
    )
    output = capsys.readouterr().out
    assert "Traceback" not in output
    assert "bad" not in output
    assert main(["incident", "list"]) == 0
    assert capsys.readouterr().out.strip() == "[]"
