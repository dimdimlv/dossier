"""LLM client for the engine — the only place that talks to the Anthropic API.

The analyzer depends on the :class:`LLMClient` protocol, not on the SDK, so unit
tests inject a fake and never hit the network (ADR-006).
"""

from __future__ import annotations

import json
from typing import Protocol

import anthropic

from dossier.config import get_anthropic_api_key, get_model
from dossier.engine.models import (
    JobRequirements,
    SemanticAssessment,
    SkillRequirement,
)
from dossier.engine.prompts import GAP_ASSESSMENT_SYSTEM, JD_EXTRACTION_SYSTEM

_MAX_TOKENS = 4096


class EngineError(Exception):
    """Raised when an engine/LLM operation fails."""


class LLMClient(Protocol):
    """The capabilities the analyzer needs from a language model."""

    def extract_requirements(
        self, jd_text: str, language: str
    ) -> JobRequirements: ...

    def assess_gaps(
        self, requirements: list[SkillRequirement], inventory_digest: str
    ) -> SemanticAssessment: ...


class AnthropicClient:
    """:class:`LLMClient` backed by the official Anthropic SDK."""

    def __init__(
        self, *, client: anthropic.Anthropic | None = None, model: str | None = None
    ) -> None:
        self._client = client or anthropic.Anthropic(api_key=get_anthropic_api_key())
        self._model = model or get_model()

    def _parse(self, system: str, user: str, schema: type) -> object:
        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
            )
        except anthropic.APIError as exc:  # network, auth, rate limit, 4xx/5xx
            raise EngineError(f"Anthropic API call failed: {exc}") from exc
        parsed = response.parsed_output
        if parsed is None:
            raise EngineError("Model returned no structured output.")
        return parsed

    def extract_requirements(self, jd_text: str, language: str) -> JobRequirements:
        user = (
            f"Preferred analysis language: {language}.\n\n"
            f"Job description:\n\n{jd_text}"
        )
        result = self._parse(JD_EXTRACTION_SYSTEM, user, JobRequirements)
        assert isinstance(result, JobRequirements)
        return result

    def assess_gaps(
        self, requirements: list[SkillRequirement], inventory_digest: str
    ) -> SemanticAssessment:
        reqs = json.dumps([r.model_dump() for r in requirements], ensure_ascii=False)
        user = (
            f"Candidate inventory digest:\n\n{inventory_digest}\n\n"
            f"Requirements to assess (JSON):\n\n{reqs}"
        )
        result = self._parse(GAP_ASSESSMENT_SYSTEM, user, SemanticAssessment)
        assert isinstance(result, SemanticAssessment)
        return result


def build_default_client() -> LLMClient:
    """Construct the production :class:`LLMClient`. CLI tests monkeypatch this."""
    return AnthropicClient()
