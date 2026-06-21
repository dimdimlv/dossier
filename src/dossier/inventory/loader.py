"""Load and validate an inventory from its on-disk representation.

Layout (under ``DOSSIER_DATA_PATH/inventory``):

    profile.yaml        # required, single object
    skills.yaml         # optional, list
    education.yaml      # optional, list
    experience/*.md     # optional, Markdown + YAML frontmatter, one role per file

Validation errors are wrapped in :class:`InventoryError`, which — unlike a raw
Pydantic error — names the offending file so problems are easy to locate.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, TypeVar

import frontmatter
import yaml
from pydantic import BaseModel, ValidationError

from dossier.inventory.models import (
    Education,
    Experience,
    Inventory,
    Profile,
    Skill,
)

M = TypeVar("M", bound=BaseModel)


class InventoryError(Exception):
    """Raised when the inventory on disk is missing files or fails validation."""


def _read_yaml(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise InventoryError(f"Missing required inventory file: {path}") from exc
    except yaml.YAMLError as exc:
        raise InventoryError(f"Invalid YAML in {path}: {exc}") from exc


def _build(model: type[M], data: Any, source: Path) -> M:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise InventoryError(f"Validation failed in {source}:\n{exc}") from exc


def _build_list(model: type[M], items: Any, source: Path) -> list[M]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise InventoryError(
            f"Expected a list in {source}, got {type(items).__name__}"
        )
    result: list[M] = []
    for index, item in enumerate(items):
        try:
            result.append(model.model_validate(item))
        except ValidationError as exc:
            raise InventoryError(
                f"Validation failed in {source} (item {index}):\n{exc}"
            ) from exc
    return result


def _load_experience(directory: Path) -> list[Experience]:
    roles: list[Experience] = []
    if not directory.is_dir():
        return roles
    for path in sorted(directory.glob("*.md")):
        post = frontmatter.load(str(path))
        data = dict(post.metadata)
        data["summary"] = post.content.strip()
        roles.append(_build(Experience, data, path))
    return roles


def _warn_unknown_skill_refs(inventory: Inventory) -> None:
    known = {s.name.casefold() for s in inventory.skills}
    known |= {alias.casefold() for s in inventory.skills for alias in s.aliases}
    for role in inventory.experience:
        referenced = set(role.skills)
        for achievement in role.achievements:
            referenced.update(achievement.skills)
        for name in sorted(referenced):
            if name.casefold() not in known:
                warnings.warn(
                    f"Experience '{role.company}' references unknown skill {name!r} "
                    f"(not found in skills.yaml)",
                    stacklevel=2,
                )


def load_inventory(inventory_dir: Path | str) -> Inventory:
    """Read, parse and validate the inventory under ``inventory_dir``."""
    inventory_dir = Path(inventory_dir)

    profile_path = inventory_dir / "profile.yaml"
    profile = _build(Profile, _read_yaml(profile_path), profile_path)

    skills_path = inventory_dir / "skills.yaml"
    skills = (
        _build_list(Skill, _read_yaml(skills_path), skills_path)
        if skills_path.exists()
        else []
    )

    education_path = inventory_dir / "education.yaml"
    education = (
        _build_list(Education, _read_yaml(education_path), education_path)
        if education_path.exists()
        else []
    )

    experience = _load_experience(inventory_dir / "experience")

    inventory = Inventory(
        profile=profile,
        skills=skills,
        experience=experience,
        education=education,
    )
    _warn_unknown_skill_refs(inventory)
    return inventory
