"""SQLAlchemy ORM models for the application tracker.

Three tables form the walking-skeleton schema (ADR-005):

- ``applications``        — one row per job application and its current status.
- ``application_events``  — the status-change timeline (for funnel analysis).
- ``documents``           — the exact CV / cover letter / JD sent, stored as a
                            hashed file in ``dossier-data`` with provenance.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _str_enum(enum_type: type[StrEnum]) -> Enum:
    """A non-native SQL enum that persists the member *value* (e.g. ``"applied"``)."""
    return Enum(
        enum_type,
        native_enum=False,
        length=20,
        values_callable=lambda members: [m.value for m in members],
    )


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    GHOSTED = "ghosted"


#: Statuses at which an application is finished — no follow-up is due.
TERMINAL_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.ACCEPTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.GHOSTED,
    }
)


class DocumentKind(StrEnum):
    CV = "cv"
    COVER_LETTER = "cover_letter"
    JOB_DESCRIPTION = "job_description"


class Base(DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200))
    status: Mapped[ApplicationStatus] = mapped_column(_str_enum(ApplicationStatus))
    source: Mapped[str | None] = mapped_column(String(100), default=None)
    location: Mapped[str | None] = mapped_column(String(200), default=None)
    work_mode: Mapped[str | None] = mapped_column(String(20), default=None)
    compensation: Mapped[str | None] = mapped_column(String(100), default=None)
    url: Mapped[str | None] = mapped_column(Text, default=None)
    applied_on: Mapped[date | None] = mapped_column(Date, default=None)
    follow_up_on: Mapped[date | None] = mapped_column(Date, default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    events: Mapped[list[ApplicationEvent]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationEvent.occurred_at",
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="Document.created_at",
    )


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE")
    )
    from_status: Mapped[ApplicationStatus | None] = mapped_column(
        _str_enum(ApplicationStatus), default=None
    )
    to_status: Mapped[ApplicationStatus] = mapped_column(_str_enum(ApplicationStatus))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    note: Mapped[str | None] = mapped_column(Text, default=None)

    application: Mapped[Application] = relationship(back_populates="events")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE")
    )
    kind: Mapped[DocumentKind] = mapped_column(_str_enum(DocumentKind))
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(100), default=None)
    language: Mapped[str | None] = mapped_column(String(20), default=None)
    inventory_commit: Mapped[str | None] = mapped_column(String(40), default=None)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    application: Mapped[Application] = relationship(back_populates="documents")
