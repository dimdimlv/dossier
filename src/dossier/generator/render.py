"""Renders a :class:`CVDraft` to Markdown via a single Jinja2 template (ADR-008)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from dossier.generator.models import CVDraft

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,  # Markdown output, not HTML
)


def render_cv_markdown(draft: CVDraft) -> str:
    """Render ``draft`` as a single Markdown document."""
    template = _env.get_template("cv.md.j2")
    return template.render(**draft.model_dump())
