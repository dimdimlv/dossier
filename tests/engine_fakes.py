"""A fake LLMClient for engine tests — no network."""

from __future__ import annotations

from dossier.engine.models import (
    CoverLetter,
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
        cover_letter: CoverLetter | None = None,
    ) -> None:
        self._requirements = requirements
        self._assessment = assessment or SemanticAssessment()
        self._tailoring = tailoring
        self._cover_letter = cover_letter
        self.assess_called = False
        self.cover_letter_recipient: str | None = None
        self.cover_letter_notes: str | None = None

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
        self.cover_letter_recipient = recipient
        self.cover_letter_notes = notes
        if self._cover_letter is not None:
            return self._cover_letter
        salutation = f"Dear {recipient}," if recipient else "Dear Hiring Manager,"
        return cover_letter_for(
            "Opening paragraph.",
            "Body paragraph.",
            "Closing paragraph.",
            salutation=salutation,
        )


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


def cover_letter_for(
    *paragraphs: str,
    salutation: str = "Dear Hiring Manager,",
    signoff: str = "Sincerely,",
) -> CoverLetter:
    return CoverLetter(
        salutation=salutation,
        body_paragraphs=list(paragraphs),
        signoff=signoff,
    )
