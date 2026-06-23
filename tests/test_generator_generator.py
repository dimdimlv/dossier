"""Tests for CV generation orchestration (LLM client faked — no network)."""

from __future__ import annotations

from pathlib import Path

import pytest
from engine_fakes import FakeLLMClient, requirements_with, tailoring_for

from dossier import engine
from dossier.generator.generator import generate_cv, generate_cv_from_jd
from dossier.generator.selector import select_experiences
from dossier.inventory import load_inventory

INVENTORY = load_inventory(Path(__file__).parent / "fixtures" / "inventory")


def _analysis(client: FakeLLMClient) -> engine.Analysis:
    return engine.analyze_jd("jd", INVENTORY, client, language="en", use_llm_gaps=False)


def test_generate_cv_uses_tailored_phrasing() -> None:
    client = FakeLLMClient(requirements_with("Python"))
    analysis = _analysis(client)
    selected = select_experiences(INVENTORY, analysis)
    client._tailoring = tailoring_for(
        *[a.id for a in selected], overrides={selected[0].id: "Rephrased achievement."}
    )

    draft = generate_cv(INVENTORY, analysis, client, language="en")

    all_statements = [a for role in draft.roles for a in role.achievements]
    assert "Rephrased achievement." in all_statements
    assert not any(s.startswith("Cut p99") for s in all_statements)
    assert draft.summary == "Tailored summary."


def test_generate_cv_raises_when_llm_drops_an_id() -> None:
    client = FakeLLMClient(requirements_with("Python"))
    analysis = _analysis(client)
    client._tailoring = tailoring_for()  # echoes back zero ids

    with pytest.raises(engine.EngineError, match="dropped"):
        generate_cv(INVENTORY, analysis, client, language="en")


def test_generate_cv_from_jd_runs_analysis_first() -> None:
    client = FakeLLMClient(requirements_with("Python"))
    draft = generate_cv_from_jd(
        "jd text", INVENTORY, client, language="en", use_llm_gaps=False
    )
    assert draft.profile.full_name == "Jane Doe"
    assert draft.roles
    assert draft.skills
