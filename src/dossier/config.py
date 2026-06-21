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
DATABASE_URL_ENV = "DOSSIER_DATABASE_URL"
FOLLOWUP_DAYS_ENV = "DOSSIER_FOLLOWUP_DAYS"

DEFAULT_FOLLOWUP_DAYS = 10


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


def get_applications_dir(load_env: bool = True) -> Path:
    """Return the path to the applications directory inside ``dossier-data``."""
    return get_data_path(load_env=load_env) / "applications"


def get_tracker_db_path(load_env: bool = True) -> Path:
    """Return the path to the application-tracker SQLite database."""
    return get_applications_dir(load_env=load_env) / "applications.db"


def get_database_url(load_env: bool = True) -> str:
    """Return the SQLAlchemy database URL for the tracker.

    A ``DOSSIER_DATABASE_URL`` override (used by tests and CI) takes precedence;
    otherwise the URL is derived from ``DOSSIER_DATA_PATH``.
    """
    if load_env:
        load_dotenv()
    override = os.environ.get(DATABASE_URL_ENV)
    if override:
        return override
    return f"sqlite:///{get_tracker_db_path(load_env=False)}"


def get_followup_days(load_env: bool = True) -> int:
    """Return the number of days after applying before a follow-up is due."""
    if load_env:
        load_dotenv()
    raw = os.environ.get(FOLLOWUP_DAYS_ENV)
    if not raw:
        return DEFAULT_FOLLOWUP_DAYS
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"{FOLLOWUP_DAYS_ENV} must be an integer, got {raw!r}"
        ) from exc
