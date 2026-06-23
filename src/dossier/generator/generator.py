"""Orchestrates CV generation: deterministic selection → LLM phrasing → CVDraft.

Mirrors ``engine.analyzer``'s hybrid shape (ADR-006/ADR-008): selection of what to
include is deterministic and offline-testable (``generator.selector``); the LLM is
used only to tailor phrasing of what was already selected.
"""

from __future__ import annotations

from dossier.engine import Analysis, EngineError, LLMClient, analyze_jd
from dossier.generator.models import CVDraft, CVRoleSection, CVSkillGroup
from dossier.generator.selector import select_experiences, select_skills
from dossier.inventory import Inventory


def generate_cv(
    inventory: Inventory,
    analysis: Analysis,
    client: LLMClient,
    *,
    language: str = "en",
) -> CVDraft:
    """Select content from ``inventory`` (using ``analysis`` for relevance), have
    the LLM tailor its phrasing, and assemble a :class:`CVDraft`."""
    selected = select_experiences(inventory, analysis)
    skill_groups = select_skills(inventory, analysis)

    tailoring = client.tailor_cv(
        full_name=inventory.profile.full_name,
        profile_summary=inventory.profile.summary,
        achievements=selected,
        role_title=analysis.requirements.role_title,
        keywords=analysis.requirements.keywords,
        language=language,
    )

    tailored_by_id = {a.id: a.statement for a in tailoring.achievements}
    missing = [a.id for a in selected if a.id not in tailored_by_id]
    if missing:
        raise EngineError(
            f"LLM dropped achievement id(s) during CV tailoring: {', '.join(missing)}"
        )

    role_order: list[int] = []
    achievements_by_role: dict[int, list[str]] = {}
    for achievement in selected:
        role_index = int(achievement.id.split("-", 1)[0])
        if role_index not in achievements_by_role:
            achievements_by_role[role_index] = []
            role_order.append(role_index)
        achievements_by_role[role_index].append(tailored_by_id[achievement.id])

    source_roles = inventory.experience_newest_first()
    roles = [
        CVRoleSection(
            company=source_roles[role_index].company,
            title=source_roles[role_index].title,
            start=source_roles[role_index].start,
            end=source_roles[role_index].end,
            location=source_roles[role_index].location,
            achievements=achievements_by_role[role_index],
        )
        for role_index in role_order
    ]

    skills = [
        CVSkillGroup(category=category, names=[skill.name for skill in skills_in_group])
        for category, skills_in_group in skill_groups
    ]

    return CVDraft(
        profile=inventory.profile,
        summary=tailoring.summary,
        roles=roles,
        skills=skills,
        education=inventory.education,
        language=language,
    )


def generate_cv_from_jd(
    jd_text: str,
    inventory: Inventory,
    client: LLMClient,
    *,
    language: str = "en",
    use_llm_gaps: bool = True,
) -> CVDraft:
    """Analyse ``jd_text`` against ``inventory``, then generate a tailored CV."""
    analysis = analyze_jd(
        jd_text, inventory, client, language=language, use_llm_gaps=use_llm_gaps
    )
    return generate_cv(inventory, analysis, client, language=language)
