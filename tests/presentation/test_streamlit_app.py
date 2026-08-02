# ruff: noqa: E501
"""Streamlit AppTest startup and boundary behavior."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_starts_against_clean_database(
    tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("SUPPORTOPS_DB_PATH", str(tmp_path / "app.db"))  # type: ignore[attr-defined]
    monkeypatch.setenv("SUPPORTOPS_EXPORT_ROOT", str(tmp_path / "exports"))  # type: ignore[attr-defined]
    app = AppTest.from_file("src/supportops/streamlit_app.py", default_timeout=10).run()
    assert not app.exception
    assert app.title[0].value == "SupportOps Command Center"
    assert app.metric[0].value == "0"
