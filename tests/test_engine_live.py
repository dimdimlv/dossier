"""Opt-in live test against the real Anthropic API.

Skipped unless ANTHROPIC_API_KEY is set, so the default suite never hits the
network. Run explicitly with a key configured to sanity-check extraction.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from dossier.engine import AnthropicClient

JD = (Path(__file__).parent / "fixtures" / "jd" / "sample-jd.txt").read_text()


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live API test",
)
def test_extract_requirements_live() -> None:
    client = AnthropicClient()
    requirements = client.extract_requirements(JD, "en")
    assert requirements.language == "en"
    names = {s.name.lower() for s in requirements.skills}
    assert any("python" in n for n in names)
