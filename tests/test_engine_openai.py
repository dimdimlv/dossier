"""Tests for OpenAIClient with a fake SDK client (no network)."""

from __future__ import annotations

from typing import Any

import openai
import pytest

from dossier.engine import EngineError, OpenAIClient
from dossier.engine.models import (
    CVTailoring,
    JobRequirements,
    SelectedAchievement,
    SemanticAssessment,
    TailoredAchievement,
)


class _Message:
    def __init__(self, parsed: Any, refusal: str | None = None) -> None:
        self.parsed = parsed
        self.refusal = refusal


class _Choice:
    def __init__(self, message: _Message) -> None:
        self.message = message


class _Completion:
    def __init__(self, message: _Message) -> None:
        self.choices = [_Choice(message)]


class _Parser:
    def __init__(self, message: _Message | None, error: Exception | None) -> None:
        self._message = message
        self._error = error
        self.calls = 0

    def parse(self, **kwargs: Any) -> _Completion:
        self.calls += 1
        if self._error is not None:
            raise self._error
        assert self._message is not None
        return _Completion(self._message)


class FakeOpenAI:
    """Mimics the shape OpenAIClient uses: beta.chat.completions.parse()."""

    def __init__(
        self, parsed: Any = None, *, refusal: str | None = None, error: Exception | None = None
    ) -> None:
        message = _Message(parsed, refusal) if error is None else None
        parser = _Parser(message, error)
        self.beta = type(
            "Beta", (), {"chat": type("Chat", (), {"completions": parser})()}
        )()
        self._parser = parser


def _client(fake: FakeOpenAI) -> OpenAIClient:
    return OpenAIClient(client=fake, model="test-model")  # type: ignore[arg-type]


def test_extract_requirements_returns_parsed() -> None:
    fake = FakeOpenAI(JobRequirements(language="en"))
    result = _client(fake).extract_requirements("jd", "en")
    assert isinstance(result, JobRequirements)
    assert fake._parser.calls == 1


def test_assess_gaps_returns_parsed() -> None:
    fake = FakeOpenAI(SemanticAssessment(suggestions=["x"]))
    result = _client(fake).assess_gaps([], "digest")
    assert isinstance(result, SemanticAssessment)
    assert result.suggestions == ["x"]


def test_refusal_becomes_engine_error() -> None:
    fake = FakeOpenAI(None, refusal="cannot help")
    with pytest.raises(EngineError, match="refused"):
        _client(fake).extract_requirements("jd", "en")


def test_sdk_error_is_wrapped() -> None:
    fake = FakeOpenAI(error=openai.OpenAIError("boom"))
    with pytest.raises(EngineError, match="OpenAI API call failed"):
        _client(fake).extract_requirements("jd", "en")


def test_none_parsed_is_engine_error() -> None:
    fake = FakeOpenAI(None)
    with pytest.raises(EngineError, match="no structured output"):
        _client(fake).extract_requirements("jd", "en")


def test_tailor_cv_returns_parsed() -> None:
    fake = FakeOpenAI(
        CVTailoring(
            summary="Tailored.",
            achievements=[TailoredAchievement(id="0-0", statement="Rephrased.")],
        )
    )
    achievement = SelectedAchievement(
        id="0-0", company="Acme", title="Engineer", original_statement="Did a thing."
    )
    result = _client(fake).tailor_cv(
        full_name="Jane Doe",
        profile_summary="Backend engineer.",
        achievements=[achievement],
        role_title="Senior Backend Engineer",
        keywords=["Python"],
        language="en",
    )
    assert isinstance(result, CVTailoring)
    assert result.achievements[0].id == "0-0"
