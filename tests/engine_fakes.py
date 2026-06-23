"""A fake LLMClient for engine tests — no network."""

from __future__ import annotations

from dossier.engine.models import (
    CVTailoring,
    JobRequirements,
    RequirementCoverage,
    SelectedAchievement,
    SemanticAssessment,
    SkillRequirement,
    TailoredAchievement,
)


class FakeLLMClient:
    """Returns canned structured output and records whether assess_gaps ran."""

    def __init__(
        self,
        requirements: JobRequirements,
        assessment: SemanticAssessment | None = None,
        tailoring: CVTailoring | None = None,
    ) -> None:
        self._requirements = requirements
        self._assessment = assessment or SemanticAssessment()
        self._tailoring = tailoring
        self.assess_called = False

    def extract_requirements(self, jd_text: str, language: str) -> JobRequirements:
        return self._requirements

    def assess_gaps(
        self, requirements: list[SkillRequirement], inventory_digest: str
    ) -> SemanticAssessment:
        self.assess_called = True
        return self._assessment

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
        if self._tailoring is not None:
            return self._tailoring
        return tailoring_for(*[a.id for a in achievements])


def requirements_with(*skills: str) -> JobRequirements:
    return JobRequirements(
        role_title="Senior Backend Engineer",
        company="Acme Corp",
        language="en",
        skills=[SkillRequirement(name=s) for s in skills],
        responsibilities=["Operate payment services"],
    )


def assessment_gap(name: str, *, suggestions: list[str] | None = None) -> SemanticAssessment:
    return SemanticAssessment(
        assessments=[RequirementCoverage(requirement=name, status="gap")],
        suggestions=suggestions or [],
    )


def tailoring_for(
    *achievement_ids: str,
    summary: str = "Tailored summary.",
    overrides: dict[str, str] | None = None,
) -> CVTailoring:
    overrides = overrides or {}
    return CVTailoring(
        summary=summary,
        achievements=[
            TailoredAchievement(id=aid, statement=overrides.get(aid, f"Tailored: {aid}"))
            for aid in achievement_ids
        ],
    )
