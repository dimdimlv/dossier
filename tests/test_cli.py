"""Tests for the `dossier inventory validate` CLI."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from dossier.cli import run

FIXTURES = Path(__file__).parent / "fixtures" / "inventory"


def test_validate_ok(capsys: pytest.CaptureFixture[str]) -> None:
    code = run(["inventory", "validate", "--path", str(FIXTURES)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Inventory OK" in out
    assert "4 skills" in out


def test_validate_broken_dir(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    inv_dir = tmp_path / "inventory"
    shutil.copytree(FIXTURES, inv_dir)
    (inv_dir / "profile.yaml").unlink()
    code = run(["inventory", "validate", "--path", str(inv_dir)])
    assert code == 1
    err = capsys.readouterr().err
    assert "profile.yaml" in err
