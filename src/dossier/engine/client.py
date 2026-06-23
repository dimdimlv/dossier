"""LLM clients for the engine — the only place that talks to a provider SDK.

The analyzer depends on the :class:`LLMClient` protocol, not on any SDK, so unit
tests inject a fake and never hit the network. Two providers are supported behind
the same protocol: Anthropic (default) and OpenAI, selected by configuration
(``DOSSIER_LLM_PROVIDER``). See ADR-006 and ADR-007.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Protocol

from dossier.config import (
    get_anthropic_api_key,
    get_model,
    get_openai_api_key,
    get_openai_model,
    get_provider,
)
from dossier.engine.models import (
    CoverLetter,
    CVTailoring,
    JobRequirements,
    SelectedAchievement,
    SemanticAssessment,
    SkillRequirement,
)
from dossier.engine.prompts import (
    COVER_LETTER_SYSTEM,
    CV_TAILORING_SYSTEM,
    GAP_ASSESSMENT_SYSTEM,
    JD_EXTRACTION_SYSTEM,
)

if TYPE_CHECKING:
    import anthropic
    import openai

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

    def tailor_cv(
        self,
        *,
        full_name: str,
        profile_summary: str | None,
        achievements: list[SelectedAchievement],
        role_title: str | None,
        keywords: list[str],
        language: str,
    ) -> CVTailoring: ...

    def draft_cover_letter(
        self,
        *,
        full_name: str,
        profile_summary: str | None,
        achievements: list[SelectedAchievement],
        role_title: str | None,
        company: str | None,
        keywords: list[str],
        responsibilities: list[str],
        recipient: str | None,
        notes: str | None,
        language: str,
    ) -> CoverLetter: ...


# ── Shared prompt construction ───────────────────────────────────────────────
def _extraction_user(jd_text: str, language: str) -> str:
    return f"Preferred analysis language: {language}.\n\nJob description:\n\n{jd_text}"


def _assessment_user(
    requirements: list[SkillRequirement], inventory_digest: str
) -> str:
    reqs = json.dumps([r.model_dump() for r in requirements], ensure_ascii=False)
    return (
        f"Candidate inventory digest:\n\n{inventory_digest}\n\n"
        f"Requirements to assess (JSON):\n\n{reqs}"
    )


def _tailoring_user(
    full_name: str,
    profile_summary: str | None,
    achievements: list[SelectedAchievement],
    role_title: str | None,
    keywords: list[str],
    language: str,
) -> str:
    items = json.dumps([a.model_dump() for a in achievements], ensure_ascii=False)
    return (
        f"Candidate: {full_name}\n"
        f"Profile summary: {profile_summary or '—'}\n"
        f"Target role: {role_title or '—'}\n"
        f"Target keywords: {', '.join(keywords) or '—'}\n"
        f"Output language: {language}\n\n"
        f"Selected achievements (JSON):\n\n{items}"
    )


def _cover_letter_user(
    full_name: str,
    profile_summary: str | None,
    achievements: list[SelectedAchievement],
    role_title: str | None,
    company: str | None,
    keywords: list[str],
    responsibilities: list[str],
    recipient: str | None,
    notes: str | None,
    language: str,
) -> str:
    items = json.dumps([a.model_dump() for a in achievements], ensure_ascii=False)
    return (
        f"Candidate: {full_name}\n"
        f"Profile summary: {profile_summary or '—'}\n"
        f"Target role: {role_title or '—'}\n"
        f"Target company: {company or '—'}\n"
        f"Recipient: {recipient or '—'}\n"
        f"Target keywords: {', '.join(keywords) or '—'}\n"
        f"Key responsibilities: {'; '.join(responsibilities) or '—'}\n"
        f"Candidate notes: {notes or '—'}\n"
        f"Output language: {language}\n\n"
        f"Achievements to draw on (JSON):\n\n{items}"
    )


class _ParsingClient:
    """Base implementing the protocol on top of a provider-specific ``_parse``."""

    _model: str

    def _parse(self, system: str, user: str, schema: type) -> object:
        raise NotImplementedError

    def extract_requirements(self, jd_text: str, language: str) -> JobRequirements:
        result = self._parse(
            JD_EXTRACTION_SYSTEM, _extraction_user(jd_text, language), JobRequirements
        )
        assert isinstance(result, JobRequirements)
        return result

    def assess_gaps(
        self, requirements: list[SkillRequirement], inventory_digest: str
    ) -> SemanticAssessment:
        result = self._parse(
            GAP_ASSESSMENT_SYSTEM,
            _assessment_user(requirements, inventory_digest),
            SemanticAssessment,
        )
        assert isinstance(result, SemanticAssessment)
        return result

    def tailor_cv(
        self,
        *,
        full_name: str,
        profile_summary: str | None,
        achievements: list[SelectedAchievement],
        role_title: str | None,
        keywords: list[str],
        language: str,
    ) -> CVTailoring:
        result = self._parse(
            CV_TAILORING_SYSTEM,
            _tailoring_user(
                full_name, profile_summary, achievements, role_title, keywords, language
            ),
            CVTailoring,
        )
        assert isinstance(result, CVTailoring)
        return result

    def draft_cover_letter(
        self,
        *,
        full_name: str,
        profile_summary: str | None,
        achievements: list[SelectedAchievement],
        role_title: str | None,
        company: str | None,
        keywords: list[str],
        responsibilities: list[str],
        recipient: str | None,
        notes: str | None,
        language: str,
    ) -> CoverLetter:
        result = self._parse(
            COVER_LETTER_SYSTEM,
            _cover_letter_user(
                full_name,
                profile_summary,
                achievements,
                role_title,
                company,
                keywords,
                responsibilities,
                recipient,
                notes,
                language,
            ),
            CoverLetter,
        )
        assert isinstance(result, CoverLetter)
        return result


class AnthropicClient(_ParsingClient):
    """:class:`LLMClient` backed by the official Anthropic SDK."""

    def __init__(
        self, *, client: anthropic.Anthropic | None = None, model: str | None = None
    ) -> None:
        import anthropic

        self._sdk = anthropic
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
        except self._sdk.APIError as exc:  # network, auth, rate limit, 4xx/5xx
            raise EngineError(f"Anthropic API call failed: {exc}") from exc
        parsed = response.parsed_output
        if parsed is None:
            raise EngineError("Model returned no structured output.")
        return parsed


class OpenAIClient(_ParsingClient):
    """:class:`LLMClient` backed by the official OpenAI SDK (structured outputs)."""

    def __init__(
        self, *, client: openai.OpenAI | None = None, model: str | None = None
    ) -> None:
        import openai

        self._sdk = openai
        self._client = client or openai.OpenAI(api_key=get_openai_api_key())
        self._model = model or get_openai_model()

    def _parse(self, system: str, user: str, schema: type) -> object:
        try:
            completion = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format=schema,
            )
        except self._sdk.OpenAIError as exc:
            raise EngineError(f"OpenAI API call failed: {exc}") from exc
        message = completion.choices[0].message
        if message.refusal:
            raise EngineError(f"OpenAI model refused the request: {message.refusal}")
        parsed = message.parsed
        if parsed is None:
            raise EngineError("Model returned no structured output.")
        return parsed


def build_default_client(provider: str | None = None) -> LLMClient:
    """Construct the configured :class:`LLMClient`. CLI tests monkeypatch this."""
    provider = provider or get_provider()
    if provider == "openai":
        return OpenAIClient()
    return AnthropicClient()
