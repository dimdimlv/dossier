"""Tests for the tracker service/repository layer."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from dossier.tracker import (
    ApplicationStatus,
    DocumentKind,
    TrackerError,
    add_application,
    attach_document,
    due_followups,
    list_applications,
    set_status,
)


def test_add_application_records_initial_event_and_followup(session: Session) -> None:
    app = add_application(
        session,
        company="Acme",
        role="Staff Engineer",
        applied_on=date(2026, 6, 1),
    )
    assert app.id is not None
    assert app.status == ApplicationStatus.APPLIED
    assert len(app.events) == 1
    assert app.events[0].from_status is None
    assert app.events[0].to_status == ApplicationStatus.APPLIED
    # follow-up = applied_on + default 10 days
    assert app.follow_up_on == date(2026, 6, 1) + timedelta(days=10)


def test_set_status_appends_event_and_clears_followup_on_terminal(
    session: Session,
) -> None:
    app = add_application(session, company="Acme", role="Engineer")
    set_status(session, app.id, ApplicationStatus.INTERVIEW, note="phone screen")
    assert app.status == ApplicationStatus.INTERVIEW
    assert app.follow_up_on is not None
    assert app.events[-1].note == "phone screen"

    set_status(session, app.id, ApplicationStatus.REJECTED)
    assert app.status == ApplicationStatus.REJECTED
    assert app.follow_up_on is None  # terminal status clears the follow-up
    assert len(app.events) == 3  # initial + interview + rejected


def test_attach_document_copies_file_and_hashes(
    session: Session, sample_cv: Path, tmp_path: Path
) -> None:
    app = add_application(session, company="Acme", role="Engineer")
    apps_dir = tmp_path / "applications"

    doc = attach_document(
        session,
        app.id,
        DocumentKind.CV,
        sample_cv,
        model="claude-sonnet-4-6",
        language="en",
        inventory_commit="deadbeef",
        applications_dir=apps_dir,
    )

    # A frozen copy exists under applications/<id>/ ...
    copied = apps_dir / str(app.id)
    files = list(copied.glob("cv-*.md"))
    assert len(files) == 1
    # ... the stored path is relative (to the dossier-data root) ...
    assert doc.path == str(files[0].relative_to(apps_dir.parent))
    assert not Path(doc.path).is_absolute()
    # ... and the sha256 matches the bytes on disk.
    expected = hashlib.sha256(sample_cv.read_bytes()).hexdigest()
    assert doc.sha256 == expected
    assert doc.model == "claude-sonnet-4-6"
    assert doc.inventory_commit == "deadbeef"


def test_attach_document_missing_file_raises(
    session: Session, tmp_path: Path
) -> None:
    app = add_application(session, company="Acme", role="Engineer")
    with pytest.raises(TrackerError, match="not found"):
        attach_document(
            session,
            app.id,
            DocumentKind.CV,
            tmp_path / "nope.md",
            applications_dir=tmp_path / "applications",
        )


def test_get_unknown_application_raises(session: Session) -> None:
    with pytest.raises(TrackerError, match="No application"):
        set_status(session, 999, ApplicationStatus.OFFER)


def test_list_and_due_followups_filter(session: Session) -> None:
    a = add_application(
        session, company="A", role="R", applied_on=date(2026, 1, 1)
    )  # follow-up 2026-01-11
    b = add_application(session, company="B", role="R")
    set_status(session, b.id, ApplicationStatus.ACCEPTED)  # terminal, no follow-up

    assert {app.id for app in list_applications(session)} == {a.id, b.id}
    assert [app.id for app in list_applications(session, status=ApplicationStatus.ACCEPTED)] == [
        b.id
    ]

    due = due_followups(session, as_of=date(2026, 2, 1))
    assert [app.id for app in due] == [a.id]  # b is terminal, excluded
