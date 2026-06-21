"""Service-layer operations for the application tracker.

These functions operate on a SQLAlchemy :class:`~sqlalchemy.orm.Session` and
encapsulate the rules that keep the tracker consistent: every status change is
recorded as an event, follow-up dates are derived from configuration, and a sent
document is copied to an immutable file with its sha256 recorded.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from dossier.config import get_applications_dir, get_data_path, get_followup_days
from dossier.tracker.models import (
    TERMINAL_STATUSES,
    Application,
    ApplicationEvent,
    ApplicationStatus,
    Document,
    DocumentKind,
)


class TrackerError(Exception):
    """Raised when a tracker operation cannot be completed."""


def _compute_follow_up(status: ApplicationStatus, applied_on: date | None) -> date | None:
    if status in TERMINAL_STATUSES:
        return None
    base = applied_on or date.today()
    return base + timedelta(days=get_followup_days())


def add_application(
    session: Session,
    *,
    company: str,
    role: str,
    status: ApplicationStatus = ApplicationStatus.APPLIED,
    applied_on: date | None = None,
    source: str | None = None,
    location: str | None = None,
    work_mode: str | None = None,
    compensation: str | None = None,
    url: str | None = None,
    notes: str | None = None,
) -> Application:
    """Create an application, its opening event, and its follow-up date."""
    if status == ApplicationStatus.APPLIED and applied_on is None:
        applied_on = date.today()

    application = Application(
        company=company,
        role=role,
        status=status,
        applied_on=applied_on,
        source=source,
        location=location,
        work_mode=work_mode,
        compensation=compensation,
        url=url,
        notes=notes,
        follow_up_on=_compute_follow_up(status, applied_on),
    )
    application.events.append(
        ApplicationEvent(from_status=None, to_status=status)
    )
    session.add(application)
    session.flush()
    return application


def get_application(session: Session, application_id: int) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise TrackerError(f"No application with id {application_id}")
    return application


def set_status(
    session: Session,
    application_id: int,
    new_status: ApplicationStatus,
    *,
    note: str | None = None,
    occurred_at: datetime | None = None,
) -> Application:
    """Transition an application to ``new_status``, recording an event."""
    application = get_application(session, application_id)
    event = ApplicationEvent(
        from_status=application.status,
        to_status=new_status,
        note=note,
    )
    if occurred_at is not None:
        event.occurred_at = occurred_at
    application.events.append(event)
    application.status = new_status
    application.follow_up_on = _compute_follow_up(new_status, application.applied_on)
    session.flush()
    return application


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _current_inventory_commit() -> str | None:
    """Best-effort git commit of the dossier-data repo, for provenance."""
    try:
        data_path = get_data_path()
    except Exception:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(data_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def attach_document(
    session: Session,
    application_id: int,
    kind: DocumentKind,
    source_file: Path,
    *,
    model: str | None = None,
    language: str | None = None,
    inventory_commit: str | None = None,
    generated_at: datetime | None = None,
    applications_dir: Path | None = None,
) -> Document:
    """Freeze ``source_file`` as the sent ``kind`` document for an application.

    The file is copied into ``applications/<id>/`` under ``dossier-data`` and its
    sha256 recorded, so the exact version sent can be analysed later even if the
    inventory changes.
    """
    application = get_application(session, application_id)

    source_file = Path(source_file)
    if not source_file.is_file():
        raise TrackerError(f"Document source file not found: {source_file}")

    root = applications_dir if applications_dir is not None else get_applications_dir()
    dest_dir = root / str(application.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%S")
    suffix = source_file.suffix or ".md"
    dest = dest_dir / f"{kind.value}-{timestamp}{suffix}"
    shutil.copy2(source_file, dest)

    document = Document(
        application_id=application.id,
        kind=kind,
        path=str(dest.relative_to(root.parent)),
        sha256=_sha256(dest),
        model=model,
        language=language,
        inventory_commit=inventory_commit
        if inventory_commit is not None
        else _current_inventory_commit(),
        generated_at=generated_at,
    )
    session.add(document)
    session.flush()
    return document


def list_applications(
    session: Session, *, status: ApplicationStatus | None = None
) -> list[Application]:
    stmt = select(Application).order_by(Application.created_at.desc())
    if status is not None:
        stmt = stmt.where(Application.status == status)
    return list(session.scalars(stmt))


def due_followups(
    session: Session, *, as_of: date | None = None
) -> list[Application]:
    """Active applications whose follow-up date has arrived."""
    as_of = as_of or date.today()
    stmt = (
        select(Application)
        .where(Application.follow_up_on.is_not(None))
        .where(Application.follow_up_on <= as_of)
        .order_by(Application.follow_up_on)
    )
    return list(session.scalars(stmt))
