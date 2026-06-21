"""Opt-in live tests against the real provider APIs.

Each is skipped unless the relevant credentials are set, so the default suite
never hits the network. Run explicitly with keys configured to sanity-check
extraction against a provider.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from dossier.engine import AnthropicClient, OpenAIClient

JD = (Path(__file__).parent / "fixtures" / "jd" / "sample-jd.txt").read_text()


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live API test",
)
def test_extract_requirements_live_anthropic() -> None:
    client = AnthropicClient()
    requirements = client.extract_requirements(JD, "en")
    assert requirements.language == "en"
    names = {s.name.lower() for s in requirements.skills}
    assert any("python" in n for n in names)


@pytest.mark.skipif(
    not (os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_MODEL")),
    reason="OPENAI_API_KEY/OPENAI_MODEL not set; skipping live API test",
)
def test_extract_requirements_live_openai() -> None:
    client = OpenAIClient()
    requirements = client.extract_requirements(JD, "en")
    names = {s.name.lower() for s in requirements.skills}
    assert any("python" in n for n in names)
