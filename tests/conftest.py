"""Shared fixtures for the tracker tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from dossier.db import session_scope
from dossier.tracker.models import Base

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """An isolated SQLite engine with the schema created via metadata."""
    from dossier.db import get_engine

    db_path = tmp_path / "applications.db"
    engine = get_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with session_scope(engine) as session:
        yield session


@pytest.fixture
def sample_cv() -> Path:
    return FIXTURES / "documents" / "sample-cv.md"
