"""Tests for the generator's render-only content models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dossier.generator.models import CVDraft, CVRoleSection, CVSkillGroup
from dossier.inventory.models import Education, Profile


def _profile() -> Profile:
    return Profile(full_name="Jane Doe", headline="Engineer", email="jane@example.com")


def test_cv_draft_minimal() -> None:
    draft = CVDraft(
        profile=_profile(),
        summary="Tailored summary.",
        roles=[
            CVRoleSection(
                company="Acme",
                title="Engineer",
                start="2021-03",
                end=None,
                achievements=["Did a thing."],
            )
        ],
        skills=[CVSkillGroup(category="language", names=["Python"])],
        education=[],
        language="en",
    )
    assert draft.roles[0].company == "Acme"
    assert draft.model is None


def test_cv_draft_unknown_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        CVDraft(
            profile=_profile(),
            summary="x",
            roles=[],
            skills=[],
            education=[],
            language="en",
            extra_field="nope",
        )  # type: ignore[call-arg]


def test_cv_draft_with_education() -> None:
    draft = CVDraft(
        profile=_profile(),
        summary="x",
        roles=[],
        skills=[],
        education=[Education(institution="Uni", degree="BSc")],
        language="en",
    )
    assert draft.education[0].institution == "Uni"
