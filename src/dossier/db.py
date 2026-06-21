"""Database engine and session helpers shared across data layers.

Currently used by the application tracker (ADR-005). The engine binds to the
SQLite database resolved from configuration; tests inject a temporary URL.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from dossier.config import get_database_url


def get_engine(url: str | None = None) -> Engine:
    """Create an :class:`Engine` for ``url`` (defaults to the configured URL)."""
    if url is None:
        url = get_database_url()
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Provide a transactional session: commit on success, roll back on error."""
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
