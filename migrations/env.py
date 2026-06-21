"""Alembic environment for the Dossier tracker database.

The database URL is resolved from application configuration
(``dossier.config.get_database_url``) so that no path is hard-coded (ADR-001).
It can be overridden for tests/CI with ``-x db_url=...`` or the
``DOSSIER_DATABASE_URL`` environment variable.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from dossier.config import get_database_url
from dossier.tracker.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_url() -> str:
    override = context.get_x_argument(as_dictionary=True).get("db_url")
    return override or get_database_url()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DBAPI)."""
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live connection."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _resolve_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
