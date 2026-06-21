"""Verify Alembic migrations create the schema and match the models."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from dossier.migrations_support import alembic_config
from dossier.tracker.models import Base


@pytest.fixture
def _db_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setenv("DOSSIER_DATABASE_URL", url)
    return url


def test_upgrade_head_creates_tables(_db_url: str) -> None:
    command.upgrade(alembic_config(), "head")
    engine = create_engine(_db_url)
    tables = set(inspect(engine).get_table_names())
    assert {"applications", "application_events", "documents"} <= tables


def test_no_model_migration_drift(_db_url: str) -> None:
    command.upgrade(alembic_config(), "head")
    engine = create_engine(_db_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diff = compare_metadata(context, Base.metadata)
    assert diff == [], f"Models and migrations have drifted: {diff}"
