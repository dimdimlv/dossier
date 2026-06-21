"""Pydantic models for the engine's JD analysis pipeline (ADR-006).

``JobRequirements`` and ``SemanticAssessment`` double as structured-output schemas
for Claude (``messages.parse(output_format=...)``), so they use only plain types and
``Literal`` enums — within the structured-output JSON-schema limits.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RequirementImportance = Literal["required", "preferred"]
CoverageStatus = Literal["covered", "partial", "gap"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SkillRequirement(_Strict):
    name: str
    importance: RequirementImportance = "required"
    category: str | None = None


class JobRequirements(_Strict):
    """Structured requirements extracted from a job description."""

    role_title: str | None = None
    company: str | None = None
    seniority: str | None = None
    location: str | None = None
    work_mode: str | None = None
    language: str = "en"  # detected language of the JD (ISO 639-1)
    years_experience: str | None = None
    skills: list[SkillRequirement] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class RequirementCoverage(_Strict):
    requirement: str
    status: CoverageStatus
    evidence: list[str] = Field(default_factory=list)
    note: str | None = None


class SemanticAssessment(_Strict):
    """The second LLM pass's verdict on requirements not matched deterministically."""

    assessments: list[RequirementCoverage] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class GapReport(_Strict):
    coverages: list[RequirementCoverage] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    summary: str = ""
    covered_count: int = 0
    total_count: int = 0


class Analysis(_Strict):
    """The full result of analysing a JD against the inventory."""

    requirements: JobRequirements
    gaps: GapReport
