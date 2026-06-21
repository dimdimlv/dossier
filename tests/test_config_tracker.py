"""Tests for tracker-related configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from dossier.config import (
    ConfigError,
    get_database_url,
    get_followup_days,
    get_tracker_db_path,
)


def test_database_url_override_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_DATABASE_URL", "sqlite:///tmp/override.db")
    assert get_database_url(load_env=False) == "sqlite:///tmp/override.db"


def test_database_url_derived_from_data_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DOSSIER_DATABASE_URL", raising=False)
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    expected = tmp_path / "applications" / "applications.db"
    assert get_database_url(load_env=False) == f"sqlite:///{expected}"
    assert get_tracker_db_path(load_env=False) == expected


def test_followup_days_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOSSIER_FOLLOWUP_DAYS", raising=False)
    assert get_followup_days(load_env=False) == 10
    monkeypatch.setenv("DOSSIER_FOLLOWUP_DAYS", "21")
    assert get_followup_days(load_env=False) == 21


def test_followup_days_invalid_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_FOLLOWUP_DAYS", "soon")
    with pytest.raises(ConfigError, match="must be an integer"):
        get_followup_days(load_env=False)
