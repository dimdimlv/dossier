"""Orchestrates the hybrid JD analysis: extract → deterministic match → LLM gaps."""

from __future__ import annotations

from dossier.engine.client import LLMClient
from dossier.engine.gaps import build_skill_vocabulary, partition_requirements
from dossier.engine.models import Analysis, GapReport, RequirementCoverage
from dossier.inventory import Inventory


def _inventory_digest(inventory: Inventory) -> str:
    """A compact, prose digest of the inventory for the gap-assessment prompt."""
    lines = ["Skills:"]
    for skill in inventory.skills:
        aliases = f" (aka {', '.join(skill.aliases)})" if skill.aliases else ""
        lines.append(f"- {skill.name} [{skill.category}, {skill.level}]{aliases}")
    lines.append("\nExperience:")
    for role in inventory.experience:
        lines.append(f"- {role.title} at {role.company}: {role.summary}")
        for achievement in role.achievements:
            lines.append(f"    • {achievement.statement}")
    return "\n".join(lines)


def analyze_jd(
    jd_text: str,
    inventory: Inventory,
    client: LLMClient,
    *,
    language: str = "en",
    use_llm_gaps: bool = True,
) -> Analysis:
    """Analyse ``jd_text`` against ``inventory`` and return an :class:`Analysis`."""
    requirements = client.extract_requirements(jd_text, language)

    vocabulary = build_skill_vocabulary(inventory)
    covered, undecided = partition_requirements(requirements.skills, vocabulary)

    coverages: list[RequirementCoverage] = list(covered)
    suggestions: list[str] = []

    if undecided:
        if use_llm_gaps:
            assessment = client.assess_gaps(undecided, _inventory_digest(inventory))
            coverages.extend(assessment.assessments)
            suggestions = assessment.suggestions
        else:
            coverages.extend(
                RequirementCoverage(requirement=req.name, status="gap")
                for req in undecided
            )

    total = len(coverages)
    covered_count = sum(1 for c in coverages if c.status == "covered")
    gap_count = sum(1 for c in coverages if c.status == "gap")
    summary = (
        f"{covered_count} of {total} skill requirements covered; {gap_count} gaps"
    )

    gaps = GapReport(
        coverages=coverages,
        suggestions=suggestions,
        summary=summary,
        covered_count=covered_count,
        total_count=total,
    )
    return Analysis(requirements=requirements, gaps=gaps)
