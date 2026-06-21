"""Helpers for running Alembic migrations programmatically.

Locates the repository's ``alembic.ini`` and ``migrations/`` relative to this
package so ``dossier db upgrade`` (and tests) can drive Alembic without relying
on the current working directory. The database URL is resolved inside
``migrations/env.py`` from configuration (``DOSSIER_DATABASE_URL`` or
``DOSSIER_DATA_PATH``).
"""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config

#: Repository root: src/dossier/migrations_support.py -> parents[2].
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def alembic_config() -> Config:
    """Return an Alembic :class:`Config` bound to this project's migrations."""
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    return config
