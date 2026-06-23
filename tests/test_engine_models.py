"""Tests for the engine Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dossier.engine.models import (
    CoverLetter,
    CVTailoring,
    JobRequirements,
    RequirementCoverage,
    SelectedAchievement,
    SkillRequirement,
    TailoredAchievement,
)


def test_skill_requirement_defaults_to_required() -> None:
    assert SkillRequirement(name="Python").importance == "required"


def test_job_requirements_minimal() -> None:
    req = JobRequirements(language="en")
    assert req.skills == []
    assert req.role_title is None


def test_bad_importance_rejected() -> None:
    with pytest.raises(ValidationError):
        SkillRequirement(name="Python", importance="mandatory")  # type: ignore[arg-type]


def test_bad_coverage_status_rejected() -> None:
    with pytest.raises(ValidationError):
        RequirementCoverage(requirement="Python", status="maybe")  # type: ignore[arg-type]


def test_unknown_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        SkillRequirement(name="Python", level="expert")  # type: ignore[call-arg]


def test_selected_achievement_minimal() -> None:
    achievement = SelectedAchievement(
        id="0-0", company="Acme", title="Engineer", original_statement="Did a thing."
    )
    assert achievement.metrics == []


def test_cv_tailoring_minimal() -> None:
    tailoring = CVTailoring(
        summary="Tailored summary.",
        achievements=[TailoredAchievement(id="0-0", statement="Rephrased.")],
    )
    assert tailoring.achievements[0].id == "0-0"


def test_cv_tailoring_unknown_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        TailoredAchievement(id="0-0", statement="x", confidence=0.9)  # type: ignore[call-arg]


def test_cover_letter_minimal() -> None:
    letter = CoverLetter(
        salutation="Dear Hiring Manager,",
        body_paragraphs=["First paragraph.", "Second paragraph."],
        signoff="Sincerely,",
    )
    assert len(letter.body_paragraphs) == 2


def test_cover_letter_unknown_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        CoverLetter(
            salutation="Dear Hiring Manager,",
            body_paragraphs=["x"],
            signoff="Sincerely,",
            tone="formal",  # type: ignore[call-arg]
        )
