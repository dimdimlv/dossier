"""End-to-end tests for `dossier analyze` (LLM client faked — no network)."""

from __future__ import annotations

from pathlib import Path

import pytest
from engine_fakes import FakeLLMClient, assessment_gap, requirements_with

from dossier import cli, engine

FIXTURES = Path(__file__).parent / "fixtures"
JD = FIXTURES / "jd" / "sample-jd.txt"
INVENTORY = FIXTURES / "inventory"


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> FakeLLMClient:
    client = FakeLLMClient(
        requirements_with("Python", "Kubernetes"),
        assessment_gap("Kubernetes", suggestions=["Emphasise platform/AWS experience"]),
    )
    monkeypatch.setattr(engine, "build_default_client", lambda provider=None: client)
    return client


def test_analyze_prints_report(
    fake_client: FakeLLMClient, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.run(["analyze", "--jd", str(JD), "--inventory", str(INVENTORY)])
    assert code == 0
    out = capsys.readouterr().out
    assert "JD analysis" in out
    assert "Python" in out
    assert "Kubernetes" in out
    assert "1 of 2" in out


def test_analyze_json(
    fake_client: FakeLLMClient, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.run(["analyze", "--jd", str(JD), "--inventory", str(INVENTORY), "--json"])
    assert code == 0
    assert '"requirements"' in capsys.readouterr().out


def test_analyze_save_writes_files(
    fake_client: FakeLLMClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    code = cli.run(
        ["analyze", "--jd", str(JD), "--inventory", str(INVENTORY), "--save"]
    )
    assert code == 0
    saved = list((tmp_path / "analysis").glob("*.json"))
    assert len(saved) == 1
    assert saved[0].with_suffix(".md").exists()


def test_analyze_missing_jd_exits_1(
    fake_client: FakeLLMClient, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.run(
        ["analyze", "--jd", str(tmp_path / "nope.txt"), "--inventory", str(INVENTORY)]
    )
    assert code == 1
    assert "not found" in capsys.readouterr().err
