"""Tests for loading an inventory from disk."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from dossier.inventory import Inventory, load_inventory
from dossier.inventory.loader import InventoryError

FIXTURES = Path(__file__).parent / "fixtures" / "inventory"


def _copy_fixtures(tmp_path: Path) -> Path:
    dest = tmp_path / "inventory"
    shutil.copytree(FIXTURES, dest)
    return dest


def test_loads_full_inventory() -> None:
    inv = load_inventory(FIXTURES)
    assert isinstance(inv, Inventory)
    assert inv.profile.full_name == "Jane Doe"
    assert len(inv.skills) == 4
    assert len(inv.experience) == 2
    assert len(inv.education) == 1


def test_markdown_body_becomes_summary() -> None:
    inv = load_inventory(FIXTURES)
    acme = next(e for e in inv.experience if e.company == "Acme Corp")
    assert "Led the platform team" in acme.summary
    assert acme.achievements[0].metrics == ["-77% p99 latency"]


def test_experience_newest_first() -> None:
    inv = load_inventory(FIXTURES)
    assert inv.experience_newest_first()[0].company == "Acme Corp"


def test_missing_required_profile_names_the_file(tmp_path: Path) -> None:
    inv_dir = _copy_fixtures(tmp_path)
    (inv_dir / "profile.yaml").unlink()
    with pytest.raises(InventoryError, match="profile.yaml"):
        load_inventory(inv_dir)


def test_malformed_entry_raises_inventory_error(tmp_path: Path) -> None:
    inv_dir = _copy_fixtures(tmp_path)
    (inv_dir / "skills.yaml").write_text(
        "- name: Python\n  category: language\n  level: wizard\n", encoding="utf-8"
    )
    with pytest.raises(InventoryError, match="skills.yaml"):
        load_inventory(inv_dir)


def test_unknown_skill_reference_warns(tmp_path: Path) -> None:
    inv_dir = _copy_fixtures(tmp_path)
    (inv_dir / "experience" / "newco-2024.md").write_text(
        "---\n"
        "company: NewCo\n"
        "title: Engineer\n"
        "start: 2024-02\n"
        "skills: [Rust]\n"
        "---\n"
        "Worked on systems programming.\n",
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="Rust"):
        load_inventory(inv_dir)
