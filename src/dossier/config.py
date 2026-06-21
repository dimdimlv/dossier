"""Runtime configuration resolved from the environment (Twelve-Factor).

Personal data lives in a separate private repository, located at runtime via the
``DOSSIER_DATA_PATH`` environment variable (ADR-001). The variable is typically
defined in a local, gitignored ``.env`` (see ``.env.example``).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

DATA_PATH_ENV = "DOSSIER_DATA_PATH"


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def get_data_path(load_env: bool = True) -> Path:
    """Return the validated path to the private ``dossier-data`` repository."""
    if load_env:
        load_dotenv()
    raw = os.environ.get(DATA_PATH_ENV)
    if not raw:
        raise ConfigError(
            f"{DATA_PATH_ENV} is not set. Copy .env.example to .env and set it to "
            "your local dossier-data checkout."
        )
    path = Path(raw).expanduser()
    if not path.exists():
        raise ConfigError(f"{DATA_PATH_ENV} points to a non-existent path: {path}")
    return path


def get_inventory_path(load_env: bool = True) -> Path:
    """Return the path to the inventory directory inside ``dossier-data``."""
    return get_data_path(load_env=load_env) / "inventory"
