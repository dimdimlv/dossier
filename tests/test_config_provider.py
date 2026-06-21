"""Tests for LLM-provider configuration."""

from __future__ import annotations

import pytest

from dossier.config import (
    ConfigError,
    get_openai_api_key,
    get_openai_model,
    get_provider,
)


def test_provider_defaults_to_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOSSIER_LLM_PROVIDER", raising=False)
    assert get_provider(load_env=False) == "anthropic"


def test_provider_override_is_lowercased(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_LLM_PROVIDER", "OpenAI")
    assert get_provider(load_env=False) == "openai"


def test_invalid_provider_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_LLM_PROVIDER", "gemini")
    with pytest.raises(ConfigError, match="not supported"):
        get_provider(load_env=False)


def test_openai_key_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        get_openai_api_key(load_env=False)


def test_openai_model_required_no_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    with pytest.raises(ConfigError, match="OPENAI_MODEL"):
        get_openai_model(load_env=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    assert get_openai_model(load_env=False) == "gpt-4o"
