"""End-to-end tests for the `dossier db` and `dossier track` CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from dossier.cli import run

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway DOSSIER_DATA_PATH with the database migrated to head."""
    monkeypatch.delenv("DOSSIER_DATABASE_URL", raising=False)
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    assert run(["db", "upgrade"]) == 0
    return tmp_path


def test_full_tracker_flow(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()  # clear the "db upgrade" output

    assert (
        run(
            [
                "track",
                "add",
                "--company",
                "Acme",
                "--role",
                "Staff Engineer",
                "--status",
                "applied",
                "--applied-on",
                "2026-06-01",
            ]
        )
        == 0
    )
    assert "Application #1 added" in capsys.readouterr().out

    cv = FIXTURES / "documents" / "sample-cv.md"
    assert run(["track", "attach", "1", "--kind", "cv", "--file", str(cv)]) == 0
    out = capsys.readouterr().out
    assert "Attached cv" in out

    # The frozen copy exists under applications/1/.
    frozen = list((data_path / "applications" / "1").glob("cv-*.md"))
    assert len(frozen) == 1

    assert run(["track", "status", "1", "interview", "--note", "phone screen"]) == 0
    assert "applied → interview" in capsys.readouterr().out

    assert run(["track", "show", "1"]) == 0
    show = capsys.readouterr().out
    assert "Acme — Staff Engineer" in show
    assert "applied → interview" in show
    assert "cv" in show

    assert run(["track", "list"]) == 0
    assert "Acme — Staff Engineer" in capsys.readouterr().out

    assert run(["track", "followups", "--as-of", "2026-12-31"]) == 0
    assert "#1" in capsys.readouterr().out


def test_status_unknown_application_exits_1(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    assert run(["track", "status", "42", "offer"]) == 1
    assert "No application" in capsys.readouterr().err
