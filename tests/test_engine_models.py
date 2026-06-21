"""Tests for the engine Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dossier.engine.models import (
    JobRequirements,
    RequirementCoverage,
    SkillRequirement,
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
