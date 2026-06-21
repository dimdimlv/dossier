"""Deterministic skill matching between JD requirements and the inventory.

This is the offline, fully-testable half of the hybrid gap analysis (ADR-006):
exact, case-insensitive matching by skill name, alias, and the skills referenced in
experience. Whatever it cannot decide is handed to the LLM pass.
"""

from __future__ import annotations

from dossier.engine.models import RequirementCoverage, SkillRequirement
from dossier.inventory import Inventory


def build_skill_vocabulary(inventory: Inventory) -> dict[str, str]:
    """Map casefolded skill terms → a canonical display label.

    Includes each skill's name and aliases, plus any skill names referenced by
    experience entries and their achievements.
    """
    vocab: dict[str, str] = {}
    for skill in inventory.skills:
        vocab[skill.name.casefold()] = skill.name
        for alias in skill.aliases:
            vocab.setdefault(alias.casefold(), skill.name)
    for role in inventory.experience:
        for name in role.skills:
            vocab.setdefault(name.casefold(), name)
        for achievement in role.achievements:
            for name in achievement.skills:
                vocab.setdefault(name.casefold(), name)
    return vocab


def match_requirement(
    requirement: SkillRequirement, vocabulary: dict[str, str]
) -> RequirementCoverage | None:
    """Return a ``covered`` coverage if the requirement matches, else ``None``."""
    label = vocabulary.get(requirement.name.casefold())
    if label is None:
        return None
    return RequirementCoverage(
        requirement=requirement.name,
        status="covered",
        evidence=[label],
        note="exact/alias match",
    )


def partition_requirements(
    requirements: list[SkillRequirement], vocabulary: dict[str, str]
) -> tuple[list[RequirementCoverage], list[SkillRequirement]]:
    """Split requirements into deterministically-covered and undecided."""
    covered: list[RequirementCoverage] = []
    undecided: list[SkillRequirement] = []
    for requirement in requirements:
        coverage = match_requirement(requirement, vocabulary)
        if coverage is None:
            undecided.append(requirement)
        else:
            covered.append(coverage)
    return covered, undecided
