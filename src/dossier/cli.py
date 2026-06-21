"""Command-line interface for Dossier.

Currently exposes ``dossier inventory validate``. Built on argparse (stdlib) to
avoid committing to a CLI framework before the engine/tracker milestones.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dossier.config import ConfigError, get_inventory_path
from dossier.inventory.loader import InventoryError, load_inventory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dossier",
        description="Generate tailored CVs and cover letters from a structured inventory.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

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
    return parser


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


def run(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and dispatch. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    if args.command == "inventory" and args.inventory_command == "validate":
        return _inventory_validate(args.path)
    return 2  # pragma: no cover - argparse enforces valid subcommands


def main() -> None:
    """Entry point for the ``dossier`` console script."""
    raise SystemExit(run())
