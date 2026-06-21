"""Tests for the hybrid analysis orchestration (no network)."""

from __future__ import annotations

from pathlib import Path

from engine_fakes import FakeLLMClient, assessment_gap, requirements_with

from dossier.engine import analyze_jd
from dossier.inventory import load_inventory

INVENTORY = load_inventory(Path(__file__).parent / "fixtures" / "inventory")


def test_hybrid_merges_deterministic_and_llm_gaps() -> None:
    client = FakeLLMClient(
        requirements_with("Python", "Kubernetes"),
        assessment_gap("Kubernetes", suggestions=["Highlight your AWS/platform work"]),
    )
    analysis = analyze_jd("jd", INVENTORY, client, language="en")

    statuses = {c.requirement: c.status for c in analysis.gaps.coverages}
    assert statuses == {"Python": "covered", "Kubernetes": "gap"}
    assert client.assess_called is True
    assert analysis.gaps.covered_count == 1
    assert analysis.gaps.total_count == 2
    assert "1 of 2" in analysis.gaps.summary
    assert analysis.gaps.suggestions == ["Highlight your AWS/platform work"]


def test_no_llm_call_when_everything_matches() -> None:
    client = FakeLLMClient(requirements_with("Python", "AWS"))
    analysis = analyze_jd("jd", INVENTORY, client)
    assert client.assess_called is False
    assert all(c.status == "covered" for c in analysis.gaps.coverages)


def test_no_llm_gaps_flag_marks_gaps_without_calling() -> None:
    client = FakeLLMClient(requirements_with("Python", "Kubernetes"))
    analysis = analyze_jd("jd", INVENTORY, client, use_llm_gaps=False)
    assert client.assess_called is False
    statuses = {c.requirement: c.status for c in analysis.gaps.coverages}
    assert statuses["Kubernetes"] == "gap"
