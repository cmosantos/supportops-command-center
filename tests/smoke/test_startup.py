import socket

import pytest

from supportops.cli import main


def test_all_foundation_commands_work_with_network_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def deny_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access is forbidden in the foundation")

    monkeypatch.setattr(socket, "create_connection", deny_network)

    assert main(["version"]) == 0
    assert main(["config", "validate"]) == 0
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "1.0.0" in output
    assert "[PASS] composition_root" in output
