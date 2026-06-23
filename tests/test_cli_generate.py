"""End-to-end tests for `dossier generate cv` (LLM client faked — no network)."""

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


def test_generate_cv_prints_markdown(
    fake_client: FakeLLMClient, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.run(
        ["generate", "cv", "--jd", str(JD), "--inventory", str(INVENTORY)]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "# Jane Doe" in out
    assert "Tailored summary." in out


def test_generate_cv_save_writes_file(
    fake_client: FakeLLMClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    code = cli.run(
        ["generate", "cv", "--jd", str(JD), "--inventory", str(INVENTORY), "--save"]
    )
    assert code == 0
    saved = list((tmp_path / "generated").glob("*.md"))
    assert len(saved) == 1
    assert "track attach" in capsys.readouterr().out


def test_generate_cv_missing_jd_exits_1(
    fake_client: FakeLLMClient, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.run(
        [
            "generate",
            "cv",
            "--jd",
            str(tmp_path / "nope.txt"),
            "--inventory",
            str(INVENTORY),
        ]
    )
    assert code == 1
    assert "not found" in capsys.readouterr().err


def test_generate_cover_letter_prints_markdown(
    fake_client: FakeLLMClient, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.run(
        [
            "generate",
            "cover-letter",
            "--jd",
            str(JD),
            "--inventory",
            str(INVENTORY),
            "--to",
            "Jane Smith",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "# Jane Doe" in out
    assert "Dear Jane Smith," in out


def test_generate_cover_letter_save_writes_file(
    fake_client: FakeLLMClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    code = cli.run(
        [
            "generate",
            "cover-letter",
            "--jd",
            str(JD),
            "--inventory",
            str(INVENTORY),
            "--save",
        ]
    )
    assert code == 0
    saved = list((tmp_path / "generated").glob("*-cover-letter-*.md"))
    assert len(saved) == 1
    assert "track attach" in capsys.readouterr().out


def test_generate_cover_letter_missing_jd_exits_1(
    fake_client: FakeLLMClient, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.run(
        [
            "generate",
            "cover-letter",
            "--jd",
            str(tmp_path / "nope.txt"),
            "--inventory",
            str(INVENTORY),
        ]
    )
    assert code == 1
    assert "not found" in capsys.readouterr().err
