"""The generator layer: assembles tailored CV and cover letter drafts from the
inventory (ADR-008, ADR-009)."""

from __future__ import annotations

from dossier.generator.generator import (
    generate_cover_letter,
    generate_cover_letter_from_jd,
    generate_cv,
    generate_cv_from_jd,
)
from dossier.generator.models import (
    CoverLetterDraft,
    CVDraft,
    CVRoleSection,
    CVSkillGroup,
)
from dossier.generator.render import render_cover_letter_markdown, render_cv_markdown

__all__ = [
    "CVDraft",
    "CVRoleSection",
    "CVSkillGroup",
    "CoverLetterDraft",
    "generate_cover_letter",
    "generate_cover_letter_from_jd",
    "generate_cv",
    "generate_cv_from_jd",
    "render_cover_letter_markdown",
    "render_cv_markdown",
]
