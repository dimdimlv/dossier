"""The engine layer: JD analysis and gap reporting via the Anthropic API."""

from __future__ import annotations

from dossier.engine.analyzer import analyze_jd
from dossier.engine.client import (
    AnthropicClient,
    EngineError,
    LLMClient,
    OpenAIClient,
    build_default_client,
)
from dossier.engine.models import (
    Analysis,
    CVTailoring,
    GapReport,
    JobRequirements,
    RequirementCoverage,
    SelectedAchievement,
    SemanticAssessment,
    SkillRequirement,
    TailoredAchievement,
)

__all__ = [
    "Analysis",
    "AnthropicClient",
    "CVTailoring",
    "EngineError",
    "GapReport",
    "JobRequirements",
    "LLMClient",
    "OpenAIClient",
    "RequirementCoverage",
    "SelectedAchievement",
    "SemanticAssessment",
    "SkillRequirement",
    "TailoredAchievement",
    "analyze_jd",
    "build_default_client",
]
