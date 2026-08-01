from pathlib import Path

import pytest

from supportops.config import Settings, load_settings
from supportops.errors import ConfigurationError


def test_settings_use_safe_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    settings = Settings()

    assert settings.environment == "local"
    assert settings.log_level == "INFO"
    assert settings.llm_enabled is False


def test_settings_support_prefixed_environment_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SUPPORTOPS_LOG_LEVEL", "WARNING")

    assert Settings().log_level == "WARNING"


def test_invalid_settings_raise_safe_actionable_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    rejected_value = "value-that-must-not-leak"
    monkeypatch.setenv("SUPPORTOPS_LOG_LEVEL", rejected_value)

    with pytest.raises(ConfigurationError) as captured:
        load_settings()

    assert "log_level" in captured.value.public_message
    assert ".env.example" in captured.value.public_message
    assert rejected_value not in captured.value.public_message


def test_llm_cannot_be_enabled_in_foundation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SUPPORTOPS_LLM_ENABLED", "true")

    with pytest.raises(ConfigurationError):
        load_settings()
