"""The generator layer: assembles tailored CV drafts from the inventory (ADR-008)."""

from __future__ import annotations

from dossier.generator.generator import generate_cv, generate_cv_from_jd
from dossier.generator.models import CVDraft, CVRoleSection, CVSkillGroup
from dossier.generator.render import render_cv_markdown

__all__ = [
    "CVDraft",
    "CVRoleSection",
    "CVSkillGroup",
    "generate_cv",
    "generate_cv_from_jd",
    "render_cv_markdown",
]
