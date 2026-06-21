"""Tests for environment-based path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from dossier.config import ConfigError, get_data_path, get_inventory_path


def test_get_data_path_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    assert get_data_path(load_env=False) == tmp_path


def test_get_inventory_path_appends_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DOSSIER_DATA_PATH", str(tmp_path))
    assert get_inventory_path(load_env=False) == tmp_path / "inventory"


def test_unset_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOSSIER_DATA_PATH", raising=False)
    with pytest.raises(ConfigError, match="DOSSIER_DATA_PATH"):
        get_data_path(load_env=False)


def test_nonexistent_path_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_DATA_PATH", "/no/such/path/xyzzy")
    with pytest.raises(ConfigError, match="non-existent"):
        get_data_path(load_env=False)
