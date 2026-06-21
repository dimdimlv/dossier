"""Tests for deterministic skill matching."""

from __future__ import annotations

from pathlib import Path

from dossier.engine.gaps import (
    build_skill_vocabulary,
    match_requirement,
    partition_requirements,
)
from dossier.engine.models import SkillRequirement
from dossier.inventory import load_inventory

INVENTORY = load_inventory(Path(__file__).parent / "fixtures" / "inventory")


def test_vocabulary_includes_aliases_and_experience_skills() -> None:
    vocab = build_skill_vocabulary(INVENTORY)
    assert "python" in vocab
    assert "py" in vocab  # alias
    assert vocab["py"] == "Python"
    assert "postgresql" in vocab  # referenced by experience too


def test_alias_match_is_covered() -> None:
    vocab = build_skill_vocabulary(INVENTORY)
    coverage = match_requirement(SkillRequirement(name="py"), vocab)
    assert coverage is not None
    assert coverage.status == "covered"
    assert coverage.evidence == ["Python"]


def test_unknown_requirement_is_undecided() -> None:
    vocab = build_skill_vocabulary(INVENTORY)
    assert match_requirement(SkillRequirement(name="Kubernetes"), vocab) is None


def test_partition_splits_covered_and_undecided() -> None:
    vocab = build_skill_vocabulary(INVENTORY)
    covered, undecided = partition_requirements(
        [SkillRequirement(name="Python"), SkillRequirement(name="Kubernetes")], vocab
    )
    assert [c.requirement for c in covered] == ["Python"]
    assert [u.name for u in undecided] == ["Kubernetes"]
