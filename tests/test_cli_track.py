"""End-to-end tests for the `dossier db` and `dossier track` CLI commands."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from dossier.cli import _parse_duration_days, run

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("spec", "expected"),
    [("7", 7), ("7d", 7), ("0d", 0), ("2w", 14), ("1w", 7)],
)
def test_parse_duration_days(spec: str, expected: int) -> None:
    assert _parse_duration_days(spec) == expected


@pytest.mark.parametrize("spec", ["", "abc", "7m", "-3", "1.5d", "w"])
def test_parse_duration_days_rejects_bad_input(spec: str) -> None:
    with pytest.raises(ValueError):
        _parse_duration_days(spec)


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


def _add_app(applied_on: str = "2026-06-01") -> None:
    assert (
        run(
            [
                "track", "add", "--company", "Acme", "--role", "Engineer",
                "--applied-on", applied_on,
            ]
        )
        == 0
    )


def test_remind_on_sets_explicit_date(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_app()
    capsys.readouterr()
    assert run(["track", "remind", "1", "--on", "2026-07-01"]) == 0
    assert "2026-07-01" in capsys.readouterr().out
    assert run(["track", "show", "1"]) == 0
    assert "2026-07-01" in capsys.readouterr().out


def test_remind_in_reschedules_relative(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_app()
    capsys.readouterr()
    assert run(["track", "remind", "1", "--in", "7d"]) == 0
    expected = (date.today() + timedelta(days=7)).isoformat()
    assert expected in capsys.readouterr().out


def test_remind_clear_dismisses_followup(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_app()
    capsys.readouterr()
    assert run(["track", "remind", "1", "--clear"]) == 0
    assert "cleared" in capsys.readouterr().out.lower()
    # No longer surfaces in the digest.
    assert run(["track", "followups", "--as-of", "2026-12-31"]) == 0
    assert "No follow-ups due" in capsys.readouterr().out


def test_remind_bad_duration_exits_1(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_app()
    capsys.readouterr()
    assert run(["track", "remind", "1", "--in", "soon"]) == 1
    assert "Invalid duration" in capsys.readouterr().err


def test_followups_digest_groups_overdue_and_due_today(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_app()  # #1
    _add_app()  # #2
    # #1 is overdue, #2 is due exactly on the as-of date.
    assert run(["track", "remind", "1", "--on", "2026-06-01"]) == 0
    assert run(["track", "remind", "2", "--on", "2026-06-10"]) == 0
    capsys.readouterr()

    assert run(["track", "followups", "--as-of", "2026-06-10"]) == 0
    out = capsys.readouterr().out
    assert "2 follow-up(s) due (1 overdue)" in out
    assert "Overdue:" in out
    assert "Due today:" in out
    assert "9d overdue" in out  # 2026-06-01 -> 2026-06-10


def test_followups_exit_code_reflects_due_items(
    data_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_app()
    assert run(["track", "remind", "1", "--on", "2026-06-01"]) == 0
    capsys.readouterr()

    # With items due and --exit-code, exit 1; without the flag, exit 0.
    assert run(["track", "followups", "--as-of", "2026-06-10", "--exit-code"]) == 1
    assert run(["track", "followups", "--as-of", "2026-06-10"]) == 0

    # No items due -> exit 0 even with --exit-code.
    assert run(["track", "remind", "1", "--clear"]) == 0
    capsys.readouterr()
    assert run(["track", "followups", "--as-of", "2026-06-10", "--exit-code"]) == 0
