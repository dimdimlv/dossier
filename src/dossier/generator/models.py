"""Render-only content models for a generated CV (no LLM-protocol concerns —
those live in :mod:`dossier.engine.models`; see ADR-008)."""

from __future__ import annotations

from datetime import date as date_
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from dossier.inventory.models import Education, Profile, SkillCategory, YearMonth


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CVRoleSection(_Strict):
    company: str
    title: str
    start: YearMonth
    end: YearMonth | None = None
    location: str | None = None
    achievements: list[str] = Field(default_factory=list)


class CVSkillGroup(_Strict):
    category: SkillCategory
    names: list[str] = Field(default_factory=list)


class CVDraft(_Strict):
    """The content of one generated CV, decoupled from the LLM that tailored its
    phrasing and from the Markdown template that renders it."""

    profile: Profile
    summary: str
    roles: list[CVRoleSection] = Field(default_factory=list)
    skills: list[CVSkillGroup] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    language: str
    model: str | None = None
    generated_at: datetime | None = None


class CoverLetterDraft(_Strict):
    """The content of one generated cover letter, decoupled from the LLM that
    composed its prose and from the Markdown template that renders it. The
    candidate's name/contact come from ``profile``, not from the LLM (ADR-009)."""

    profile: Profile
    salutation: str
    body_paragraphs: list[str] = Field(default_factory=list)
    signoff: str
    recipient: str | None = None
    company: str | None = None
    role_title: str | None = None
    date: date_ | None = None
    language: str
    model: str | None = None
    generated_at: datetime | None = None
