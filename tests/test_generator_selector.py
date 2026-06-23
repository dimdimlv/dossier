"""Tests for deterministic CV content selection (no LLM, no client)."""

from __future__ import annotations

from pathlib import Path

from dossier.engine.models import (
    Analysis,
    GapReport,
    JobRequirements,
    SkillRequirement,
)
from dossier.generator.selector import select_experiences, select_skills
from dossier.inventory import load_inventory

INVENTORY = load_inventory(Path(__file__).parent / "fixtures" / "inventory")


def _analysis(*skills: str, keywords: list[str] | None = None) -> Analysis:
    return Analysis(
        requirements=JobRequirements(
            language="en",
            skills=[SkillRequirement(name=s) for s in skills],
            keywords=keywords or [],
        ),
        gaps=GapReport(),
    )


def test_select_experiences_orders_roles_newest_first() -> None:
    selected = select_experiences(INVENTORY, _analysis("Python"))
    companies = [a.company for a in selected]
    assert companies.index("Acme Corp") < companies.index("Globex")


def test_select_experiences_prefers_matching_skill_and_metrics() -> None:
    selected = select_experiences(
        INVENTORY, _analysis("Python"), max_achievements_per_role=1
    )
    acme = [a for a in selected if a.company == "Acme Corp"]
    assert len(acme) == 1
    assert acme[0].original_statement.startswith("Cut p99")
    assert acme[0].id == "0-0"


def test_select_experiences_without_analysis_falls_back_to_metrics() -> None:
    selected = select_experiences(INVENTORY, None, max_achievements_per_role=1)
    acme = [a for a in selected if a.company == "Acme Corp"]
    assert acme[0].original_statement.startswith("Cut p99")


def test_select_experiences_respects_max_roles() -> None:
    selected = select_experiences(INVENTORY, _analysis("Python"), max_roles=1)
    assert {a.company for a in selected} == {"Acme Corp"}


def test_select_skills_groups_by_category_relevant_first() -> None:
    groups = select_skills(INVENTORY, _analysis("Python"))
    categories = [category for category, _ in groups]
    assert categories[0] == "language"
    language_skills = dict(groups)["language"]
    assert language_skills[0].name == "Python"


def test_select_skills_without_analysis_preserves_original_order() -> None:
    groups = select_skills(INVENTORY, None)
    categories = [category for category, _ in groups]
    assert categories == ["language", "platform", "tool", "soft"]
