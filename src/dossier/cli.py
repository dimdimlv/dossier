"""Command-line interface for Dossier.

Exposes ``dossier inventory validate``, ``dossier db upgrade`` and the
``dossier track`` family. Built on argparse (stdlib) to avoid committing to a CLI
framework before the engine milestone.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from dossier import engine
from dossier.config import (
    DATABASE_URL_ENV,
    ConfigError,
    get_analysis_dir,
    get_applications_dir,
    get_default_language,
    get_inventory_path,
)
from dossier.db import get_engine, session_scope
from dossier.inventory.loader import InventoryError, load_inventory
from dossier.tracker import (
    ApplicationStatus,
    DocumentKind,
    TrackerError,
    add_application,
    attach_document,
    due_followups,
    get_application,
    list_applications,
    set_status,
)

_STATUS_CHOICES = [s.value for s in ApplicationStatus]
_KIND_CHOICES = [k.value for k in DocumentKind]


# ── Parser ───────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dossier",
        description="Generate tailored CVs and cover letters from a structured inventory.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    # inventory
    inventory = commands.add_parser("inventory", help="Inventory commands")
    inventory_commands = inventory.add_subparsers(
        dest="inventory_command", required=True
    )
    validate = inventory_commands.add_parser(
        "validate", help="Load and validate the inventory"
    )
    validate.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Inventory directory (defaults to $DOSSIER_DATA_PATH/inventory)",
    )

    # db
    db = commands.add_parser("db", help="Database commands")
    db_commands = db.add_subparsers(dest="db_command", required=True)
    db_commands.add_parser("upgrade", help="Create or upgrade the database to head")

    # track
    track = commands.add_parser("track", help="Application tracker commands")
    track_commands = track.add_subparsers(dest="track_command", required=True)

    add = track_commands.add_parser("add", help="Add an application")
    add.add_argument("--company", required=True)
    add.add_argument("--role", required=True)
    add.add_argument("--status", choices=_STATUS_CHOICES, default="applied")
    add.add_argument("--applied-on", type=date.fromisoformat, default=None)
    add.add_argument("--source", default=None)
    add.add_argument("--url", default=None)
    add.add_argument("--location", default=None)
    add.add_argument("--work-mode", default=None)
    add.add_argument("--comp", dest="compensation", default=None)
    add.add_argument("--notes", default=None)

    status = track_commands.add_parser("status", help="Change an application's status")
    status.add_argument("id", type=int)
    status.add_argument("new_status", choices=_STATUS_CHOICES)
    status.add_argument("--note", default=None)

    attach = track_commands.add_parser("attach", help="Attach a sent document")
    attach.add_argument("id", type=int)
    attach.add_argument("--kind", choices=_KIND_CHOICES, required=True)
    attach.add_argument("--file", type=Path, required=True)
    attach.add_argument("--model", default=None)
    attach.add_argument("--language", default=None)

    listing = track_commands.add_parser("list", help="List applications")
    listing.add_argument("--status", choices=_STATUS_CHOICES, default=None)

    show = track_commands.add_parser("show", help="Show an application in detail")
    show.add_argument("id", type=int)

    followups = track_commands.add_parser(
        "followups", help="List applications with a due follow-up"
    )
    followups.add_argument("--as-of", type=date.fromisoformat, default=None)

    # analyze
    analyze = commands.add_parser(
        "analyze", help="Analyse a job description against the inventory"
    )
    analyze.add_argument("--jd", required=True, help="JD file path, or '-' for stdin")
    analyze.add_argument(
        "--inventory",
        type=Path,
        default=None,
        help="Inventory directory (defaults to $DOSSIER_DATA_PATH/inventory)",
    )
    analyze.add_argument("--language", default=None, help="Analysis language (ISO 639-1)")
    analyze.add_argument(
        "--json", action="store_true", dest="as_json", help="Output JSON"
    )
    analyze.add_argument(
        "--save", action="store_true", help="Save JSON + markdown under DOSSIER_DATA_PATH"
    )
    analyze.add_argument(
        "--no-llm-gaps",
        action="store_true",
        dest="no_llm_gaps",
        help="Deterministic matching only (no second API call)",
    )

    return parser


# ── Inventory ────────────────────────────────────────────────────────────────
def _inventory_validate(path: Path | None) -> int:
    try:
        inventory_dir = path if path is not None else get_inventory_path()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    try:
        inventory = load_inventory(inventory_dir)
    except InventoryError as exc:
        print(f"Inventory is invalid:\n{exc}", file=sys.stderr)
        return 1
    print(
        f"✓ Inventory OK — {len(inventory.skills)} skills, "
        f"{len(inventory.experience)} roles, "
        f"{len(inventory.education)} education entries"
    )
    return 0


# ── Tracker ──────────────────────────────────────────────────────────────────
@contextmanager
def _session() -> Iterator[Session]:
    with session_scope(get_engine()) as session:
        yield session


def _db_upgrade() -> int:
    from alembic import command

    from dossier.migrations_support import alembic_config

    try:
        if not os.environ.get(DATABASE_URL_ENV):
            get_applications_dir().mkdir(parents=True, exist_ok=True)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    command.upgrade(alembic_config(), "head")
    print("✓ Database upgraded to head")
    return 0


def _track_add(args: argparse.Namespace) -> int:
    with _session() as session:
        application = add_application(
            session,
            company=args.company,
            role=args.role,
            status=ApplicationStatus(args.status),
            applied_on=args.applied_on,
            source=args.source,
            url=args.url,
            location=args.location,
            work_mode=args.work_mode,
            compensation=args.compensation,
            notes=args.notes,
        )
        print(
            f"✓ Application #{application.id} added: "
            f"{application.company} — {application.role} [{application.status.value}]"
        )
    return 0


def _track_status(args: argparse.Namespace) -> int:
    with _session() as session:
        application = set_status(
            session, args.id, ApplicationStatus(args.new_status), note=args.note
        )
        previous = application.events[-1].from_status
        previous_label = previous.value if previous is not None else "—"
        print(
            f"✓ Application #{application.id}: "
            f"{previous_label} → {application.status.value}"
        )
    return 0


def _track_attach(args: argparse.Namespace) -> int:
    with _session() as session:
        document = attach_document(
            session,
            args.id,
            DocumentKind(args.kind),
            args.file,
            model=args.model,
            language=args.language,
        )
        print(
            f"✓ Attached {document.kind.value} to application #{args.id} "
            f"(sha256 {document.sha256[:12]}…) → {document.path}"
        )
    return 0


def _track_list(args: argparse.Namespace) -> int:
    status = ApplicationStatus(args.status) if args.status else None
    with _session() as session:
        applications = list_applications(session, status=status)
        if not applications:
            print("No applications found.")
            return 0
        for app in applications:
            applied = app.applied_on.isoformat() if app.applied_on else "—"
            print(
                f"#{app.id:<3} {app.status.value:<10} "
                f"{app.company} — {app.role}  (applied {applied})"
            )
    return 0


def _track_show(application_id: int) -> int:
    with _session() as session:
        app = get_application(session, application_id)
        print(f"Application #{app.id}: {app.company} — {app.role}")
        print(f"  Status:    {app.status.value}")
        print(f"  Applied:   {app.applied_on.isoformat() if app.applied_on else '—'}")
        print(
            f"  Follow-up: {app.follow_up_on.isoformat() if app.follow_up_on else '—'}"
        )
        if app.source:
            print(f"  Source:    {app.source}")
        if app.url:
            print(f"  URL:       {app.url}")
        print("  Timeline:")
        for event in app.events:
            origin = event.from_status.value if event.from_status else "—"
            note = f"  ({event.note})" if event.note else ""
            print(
                f"    {event.occurred_at:%Y-%m-%d %H:%M} "
                f"{origin} → {event.to_status.value}{note}"
            )
        print("  Documents:")
        if not app.documents:
            print("    (none)")
        for doc in app.documents:
            print(
                f"    {doc.kind.value:<16} {doc.path}  "
                f"[sha256 {doc.sha256[:12]}…]"
            )
    return 0


def _track_followups(as_of: date | None) -> int:
    with _session() as session:
        applications = due_followups(session, as_of=as_of)
        if not applications:
            print("No follow-ups due.")
            return 0
        print(f"{len(applications)} follow-up(s) due:")
        for app in applications:
            due = app.follow_up_on.isoformat() if app.follow_up_on else "—"
            print(
                f"#{app.id:<3} due {due}  {app.company} — {app.role} "
                f"[{app.status.value}]"
            )
    return 0


def _dispatch_track(args: argparse.Namespace) -> int:
    match args.track_command:
        case "add":
            return _track_add(args)
        case "status":
            return _track_status(args)
        case "attach":
            return _track_attach(args)
        case "list":
            return _track_list(args)
        case "show":
            return _track_show(args.id)
        case "followups":
            return _track_followups(args.as_of)
    return 2  # pragma: no cover


# ── Analyze ──────────────────────────────────────────────────────────────────
def _slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "jd"


def _analysis_to_markdown(analysis: engine.Analysis) -> str:
    req = analysis.requirements
    gaps = analysis.gaps
    lines = [
        f"# JD analysis — {req.role_title or 'role'}"
        f"{f' at {req.company}' if req.company else ''}",
        "",
        f"- Language: {req.language}",
        f"- Seniority: {req.seniority or '—'}",
        f"- Location: {req.location or '—'}  |  Work mode: {req.work_mode or '—'}",
        f"- Experience: {req.years_experience or '—'}",
        "",
        f"**Coverage:** {gaps.summary}",
        "",
        "## Requirement coverage",
    ]
    icons = {"covered": "✓", "partial": "~", "gap": "✗"}
    for c in gaps.coverages:
        evidence = f" — {', '.join(c.evidence)}" if c.evidence else ""
        note = f" ({c.note})" if c.note else ""
        lines.append(f"- {icons.get(c.status, '?')} {c.requirement}{evidence}{note}")
    if gaps.suggestions:
        lines += ["", "## Suggestions to emphasise", *(f"- {s}" for s in gaps.suggestions)]
    if req.responsibilities:
        lines += ["", "## Responsibilities", *(f"- {r}" for r in req.responsibilities)]
    return "\n".join(lines) + "\n"


def _analyze(args: argparse.Namespace) -> int:
    if args.jd == "-":
        jd_text = sys.stdin.read()
    else:
        jd_path = Path(args.jd)
        if not jd_path.is_file():
            print(f"JD file not found: {jd_path}", file=sys.stderr)
            return 1
        jd_text = jd_path.read_text(encoding="utf-8")

    inventory_dir = args.inventory if args.inventory is not None else get_inventory_path()
    try:
        inventory = load_inventory(inventory_dir)
    except InventoryError as exc:
        print(f"Inventory is invalid:\n{exc}", file=sys.stderr)
        return 1

    language = args.language or get_default_language()
    client = engine.build_default_client()
    analysis = engine.analyze_jd(
        jd_text,
        inventory,
        client,
        language=language,
        use_llm_gaps=not args.no_llm_gaps,
    )

    if args.as_json:
        print(analysis.model_dump_json(indent=2))
    else:
        print(_analysis_to_markdown(analysis))

    if args.save:
        req = analysis.requirements
        stem = _slug(req.company or req.role_title or "jd")
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%S")
        out_dir = get_analysis_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        base = out_dir / f"{stem}-{timestamp}"
        base.with_suffix(".json").write_text(
            analysis.model_dump_json(indent=2), encoding="utf-8"
        )
        base.with_suffix(".md").write_text(
            _analysis_to_markdown(analysis), encoding="utf-8"
        )
        print(f"✓ Saved analysis to {base.with_suffix('.json')} and .md")

    return 0


# ── Entry point ──────────────────────────────────────────────────────────────
def run(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and dispatch. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "inventory":
            return _inventory_validate(args.path)
        if args.command == "db":
            return _db_upgrade()
        if args.command == "track":
            return _dispatch_track(args)
        if args.command == "analyze":
            return _analyze(args)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except TrackerError as exc:
        print(f"Tracker error: {exc}", file=sys.stderr)
        return 1
    except engine.EngineError as exc:
        print(f"Engine error: {exc}", file=sys.stderr)
        return 1
    return 2  # pragma: no cover - argparse enforces valid subcommands


def main() -> None:
    """Entry point for the ``dossier`` console script."""
    raise SystemExit(run())
