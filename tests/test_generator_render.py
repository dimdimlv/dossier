"""Tests for Markdown rendering of a CVDraft (no LLM, no client)."""

from __future__ import annotations

from dossier.generator.models import CVDraft, CVRoleSection, CVSkillGroup
from dossier.generator.render import render_cv_markdown
from dossier.inventory.models import Education, Link, Profile


def _draft() -> CVDraft:
    return CVDraft(
        profile=Profile(
            full_name="Jane Doe",
            headline="Staff Software Engineer",
            email="jane.doe@example.com",
            location="Riga, Latvia",
        ),
        summary="A tailored summary sentence.",
        roles=[
            CVRoleSection(
                company="Acme Corp",
                title="Staff Engineer",
                start="2021-03",
                end="2024-01",
                location="Riga, LV",
                achievements=["Cut latency significantly."],
            )
        ],
        skills=[CVSkillGroup(category="language", names=["Python"])],
        education=[Education(institution="University of Examplia", degree="BSc CS")],
        language="en",
    )


def test_render_includes_profile_header() -> None:
    md = render_cv_markdown(_draft())
    assert "# Jane Doe" in md
    assert "Staff Software Engineer" in md


def test_render_includes_summary() -> None:
    md = render_cv_markdown(_draft())
    assert "A tailored summary sentence." in md


def test_render_includes_role_section() -> None:
    md = render_cv_markdown(_draft())
    assert "Acme Corp" in md
    assert "Staff Engineer" in md
    assert "2021-03" in md
    assert "Cut latency significantly." in md


def test_render_includes_skills_grouped() -> None:
    md = render_cv_markdown(_draft())
    assert "Python" in md


def test_render_includes_education() -> None:
    md = render_cv_markdown(_draft())
    assert "University of Examplia" in md
    assert "BSc CS" in md


def test_render_separates_email_from_links_with_a_line_break() -> None:
    draft = CVDraft(
        profile=Profile(
            full_name="Jane Doe",
            headline="Staff Software Engineer",
            email="jane.doe@example.com",
            links=[Link(label="GitHub", url="https://github.com/janedoe")],
        ),
        summary="x",
        roles=[],
        skills=[],
        education=[],
        language="en",
    )
    md = render_cv_markdown(draft)
    assert "jane.doe@example.com[GitHub]" not in md
