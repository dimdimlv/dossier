"""Deterministic selection of inventory content for CV generation.

Selection happens here, in plain Python, fully offline-testable — the LLM step
(``engine.LLMClient.tailor_cv``) only rephrases what has already been chosen; it
never decides what to include or exclude (see ADR-008).
"""

from __future__ import annotations

from dossier.engine.models import Analysis, SelectedAchievement
from dossier.inventory.models import Achievement, Inventory, Skill, SkillCategory

DEFAULT_MAX_ACHIEVEMENTS_PER_ROLE = 3


def _relevant_terms(analysis: Analysis | None) -> set[str]:
    if analysis is None:
        return set()
    terms = {req.name.casefold() for req in analysis.requirements.skills}
    terms.update(k.casefold() for k in analysis.requirements.keywords)
    return terms


def _achievement_score(achievement: Achievement, terms: set[str]) -> tuple[int, int]:
    overlap = sum(1 for s in achievement.skills if s.casefold() in terms)
    has_metrics = 1 if achievement.metrics else 0
    return (overlap, has_metrics)


def select_experiences(
    inventory: Inventory,
    analysis: Analysis | None = None,
    *,
    max_roles: int | None = None,
    max_achievements_per_role: int = DEFAULT_MAX_ACHIEVEMENTS_PER_ROLE,
) -> list[SelectedAchievement]:
    """Pick which roles/achievements go into the CV, newest-first, most relevant
    achievements per role first. ``analysis`` is optional: without it, selection
    falls back to ranking achievements by presence of metrics only."""
    terms = _relevant_terms(analysis)
    roles = inventory.experience_newest_first()
    if max_roles is not None:
        roles = roles[:max_roles]

    selected: list[SelectedAchievement] = []
    for role_index, role in enumerate(roles):
        ranked = sorted(
            enumerate(role.achievements),
            key=lambda pair: (
                -_achievement_score(pair[1], terms)[0],
                -_achievement_score(pair[1], terms)[1],
                pair[0],
            ),
        )
        for achievement_index, achievement in ranked[:max_achievements_per_role]:
            selected.append(
                SelectedAchievement(
                    id=f"{role_index}-{achievement_index}",
                    company=role.company,
                    title=role.title,
                    original_statement=achievement.statement,
                    metrics=achievement.metrics,
                )
            )
    return selected


def select_skills(
    inventory: Inventory, analysis: Analysis | None = None
) -> list[tuple[SkillCategory, list[Skill]]]:
    """Group skills by category, relevant categories and skills surfaced first.
    Category and within-category order is otherwise the inventory's original
    order (stable sort), so output is unsurprising without a matching JD."""
    terms = _relevant_terms(analysis)

    def matches(skill: Skill) -> bool:
        names = {skill.name.casefold(), *(a.casefold() for a in skill.aliases)}
        return bool(names & terms)

    groups: dict[SkillCategory, list[Skill]] = {}
    order: list[SkillCategory] = []
    for skill in inventory.skills:
        if skill.category not in groups:
            groups[skill.category] = []
            order.append(skill.category)
        groups[skill.category].append(skill)

    for skills in groups.values():
        skills.sort(key=lambda s: not matches(s))
    order.sort(key=lambda category: not any(matches(s) for s in groups[category]))

    return [(category, groups[category]) for category in order]
