"""Tests that the client factory selects the configured provider (offline)."""

from __future__ import annotations

import pytest

from dossier.engine import AnthropicClient, OpenAIClient, build_default_client


@pytest.fixture(autouse=True)
def _dummy_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    # SDK constructors accept a key without making a network call.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")


def test_defaults_to_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOSSIER_LLM_PROVIDER", raising=False)
    assert isinstance(build_default_client(), AnthropicClient)


def test_openai_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_LLM_PROVIDER", "openai")
    assert isinstance(build_default_client(), OpenAIClient)


def test_explicit_provider_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_LLM_PROVIDER", "anthropic")
    assert isinstance(build_default_client(provider="openai"), OpenAIClient)
    assert isinstance(build_default_client(provider="anthropic"), AnthropicClient)
