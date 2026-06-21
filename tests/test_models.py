"""Unit tests for the inventory Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dossier.inventory import Education, Experience, Skill


def test_experience_accepts_year_month_and_year_only() -> None:
    exp = Experience(company="Acme", title="Engineer", start="2021-03", end="2024-01")
    assert exp.start == "2021-03"
    assert exp.end == "2024-01"
    assert Education(institution="U", degree="BSc", start="2010").start == "2010"


def test_year_only_integer_is_coerced_to_string() -> None:
    # Unquoted years in YAML parse as int; the model should accept them.
    exp = Experience(company="Acme", title="Engineer", start=2021)  # type: ignore[arg-type]
    assert exp.start == "2021"


@pytest.mark.parametrize("bad", ["21-3", "2021-13", "2021-00", "not-a-date", "2021-3"])
def test_invalid_year_month_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        Experience(company="Acme", title="Engineer", start=bad)


def test_end_none_means_current_role() -> None:
    exp = Experience(company="Acme", title="Engineer", start="2021-03")
    assert exp.end is None
    assert exp.is_current is True


def test_invalid_skill_level_and_category_rejected() -> None:
    with pytest.raises(ValidationError):
        Skill(name="Python", category="language", level="wizard")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Skill(name="Python", category="spell", level="expert")  # type: ignore[arg-type]


def test_unknown_field_is_forbidden() -> None:
    with pytest.raises(ValidationError):
        Skill(name="Python", category="language", level="expert", proficiency="high")  # type: ignore[call-arg]
