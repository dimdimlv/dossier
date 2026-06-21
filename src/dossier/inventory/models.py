"""Pydantic models describing the professional inventory.

The inventory is the structured source of truth from which tailored CVs and cover
letters are later assembled. Schema scope is deliberately a walking skeleton:
``Profile``, ``Skill``, ``Experience`` (with embedded ``Achievement``s) and
``Education`` — enough to generate a first CV. See ADR-004.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# ── YearMonth ────────────────────────────────────────────────────────────────
# CV dates are month-precision at most. We accept "YYYY" or "YYYY-MM" as a
# human-friendly string rather than forcing full calendar dates. Unquoted years
# in YAML parse as ``int``; those are coerced to ``str``.

_YEAR_MONTH_RE = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")


def _validate_year_month(value: object) -> str:
    if isinstance(value, int):
        value = str(value)
    if not isinstance(value, str) or not _YEAR_MONTH_RE.match(value):
        raise ValueError(f"expected 'YYYY' or 'YYYY-MM', got {value!r}")
    return value


YearMonth = Annotated[str, BeforeValidator(_validate_year_month)]


def year_month_key(value: str) -> tuple[int, int]:
    """Return a sortable ``(year, month)`` tuple; year-only sorts as month 1."""
    year, _, month = value.partition("-")
    return (int(year), int(month) if month else 1)


SkillCategory = Literal[
    "language", "framework", "tool", "platform", "domain", "method", "soft"
]
SkillLevel = Literal["beginner", "intermediate", "advanced", "expert"]


class _Strict(BaseModel):
    """Base model that rejects unknown fields so typos fail loudly."""

    model_config = ConfigDict(extra="forbid")


class Link(_Strict):
    label: str
    url: str


class Profile(_Strict):
    full_name: str
    headline: str
    summary: str | None = None
    email: str
    phone: str | None = None
    location: str | None = None
    links: list[Link] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class Skill(_Strict):
    name: str
    category: SkillCategory
    level: SkillLevel
    years: float | None = None
    last_used: int | None = None
    aliases: list[str] = Field(default_factory=list)


class Achievement(_Strict):
    statement: str
    metrics: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class Experience(_Strict):
    company: str
    title: str
    start: YearMonth
    end: YearMonth | None = None
    location: str | None = None
    employment_type: str | None = None
    skills: list[str] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    summary: str = ""

    @property
    def is_current(self) -> bool:
        return self.end is None


class Education(_Strict):
    institution: str
    degree: str
    field: str | None = None
    start: YearMonth | None = None
    end: YearMonth | None = None
    location: str | None = None
    details: str | None = None


class Inventory(_Strict):
    """Aggregate root: the whole inventory loaded into memory."""

    profile: Profile
    skills: list[Skill] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)

    def experience_newest_first(self) -> list[Experience]:
        return sorted(
            self.experience, key=lambda e: year_month_key(e.start), reverse=True
        )
