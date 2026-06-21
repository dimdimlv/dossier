"""Tests for the tracker ORM models."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from dossier.tracker.models import (
    Application,
    ApplicationEvent,
    ApplicationStatus,
    Document,
    DocumentKind,
)


def test_enum_persists_as_value(engine: Engine, session: Session, tmp_path: Path) -> None:
    app = Application(
        company="Acme", role="Engineer", status=ApplicationStatus.APPLIED
    )
    session.add(app)
    session.flush()
    app_id = app.id
    session.commit()

    # Read the raw stored value with a plain sqlite connection.
    raw = sqlite3.connect(str(engine.url.database))
    stored = raw.execute(
        "SELECT status FROM applications WHERE id = ?", (app_id,)
    ).fetchone()[0]
    raw.close()
    assert stored == "applied"  # the StrEnum value, not the member name "APPLIED"


def test_timestamps_are_populated(session: Session) -> None:
    app = Application(company="Acme", role="Engineer", status=ApplicationStatus.DRAFT)
    session.add(app)
    session.flush()
    assert app.created_at is not None
    assert app.updated_at is not None


def test_cascade_delete_removes_children(session: Session) -> None:
    app = Application(company="Acme", role="Engineer", status=ApplicationStatus.APPLIED)
    app.events.append(
        ApplicationEvent(from_status=None, to_status=ApplicationStatus.APPLIED)
    )
    app.documents.append(
        Document(kind=DocumentKind.CV, path="applications/1/cv.md", sha256="abc")
    )
    session.add(app)
    session.flush()

    session.delete(app)
    session.flush()

    assert session.query(ApplicationEvent).count() == 0
    assert session.query(Document).count() == 0


def test_date_column_round_trips(session: Session) -> None:
    app = Application(
        company="Acme",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        applied_on=date(2026, 6, 21),
    )
    session.add(app)
    session.flush()
    session.refresh(app)
    assert app.applied_on == date(2026, 6, 21)
