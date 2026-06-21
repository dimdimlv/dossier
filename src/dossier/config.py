"""Runtime configuration resolved from the environment (Twelve-Factor).

Personal data lives in a separate private repository, located at runtime via the
``DOSSIER_DATA_PATH`` environment variable (ADR-001). The variable is typically
defined in a local, gitignored ``.env`` (see ``.env.example``).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

DATA_PATH_ENV = "DOSSIER_DATA_PATH"
DATABASE_URL_ENV = "DOSSIER_DATABASE_URL"
FOLLOWUP_DAYS_ENV = "DOSSIER_FOLLOWUP_DAYS"
MODEL_ENV = "ANTHROPIC_MODEL"
API_KEY_ENV = "ANTHROPIC_API_KEY"  # pragma: allowlist secret
LANGUAGE_ENV = "DOSSIER_DEFAULT_LANGUAGE"
PROVIDER_ENV = "DOSSIER_LLM_PROVIDER"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"  # pragma: allowlist secret
OPENAI_MODEL_ENV = "OPENAI_MODEL"

DEFAULT_FOLLOWUP_DAYS = 10
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_LANGUAGE = "en"
DEFAULT_PROVIDER = "anthropic"
SUPPORTED_PROVIDERS = ("anthropic", "openai")


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def get_data_path(load_env: bool = True) -> Path:
    """Return the validated path to the private ``dossier-data`` repository."""
    if load_env:
        load_dotenv()
    raw = os.environ.get(DATA_PATH_ENV)
    if not raw:
        raise ConfigError(
            f"{DATA_PATH_ENV} is not set. Copy .env.example to .env and set it to "
            "your local dossier-data checkout."
        )
    path = Path(raw).expanduser()
    if not path.exists():
        raise ConfigError(f"{DATA_PATH_ENV} points to a non-existent path: {path}")
    return path


def get_inventory_path(load_env: bool = True) -> Path:
    """Return the path to the inventory directory inside ``dossier-data``."""
    return get_data_path(load_env=load_env) / "inventory"


def get_applications_dir(load_env: bool = True) -> Path:
    """Return the path to the applications directory inside ``dossier-data``."""
    return get_data_path(load_env=load_env) / "applications"


def get_tracker_db_path(load_env: bool = True) -> Path:
    """Return the path to the application-tracker SQLite database."""
    return get_applications_dir(load_env=load_env) / "applications.db"


def get_database_url(load_env: bool = True) -> str:
    """Return the SQLAlchemy database URL for the tracker.

    A ``DOSSIER_DATABASE_URL`` override (used by tests and CI) takes precedence;
    otherwise the URL is derived from ``DOSSIER_DATA_PATH``.
    """
    if load_env:
        load_dotenv()
    override = os.environ.get(DATABASE_URL_ENV)
    if override:
        return override
    return f"sqlite:///{get_tracker_db_path(load_env=False)}"


def get_analysis_dir(load_env: bool = True) -> Path:
    """Return the path to the saved-analysis directory inside ``dossier-data``."""
    return get_data_path(load_env=load_env) / "analysis"


def get_model(load_env: bool = True) -> str:
    """Return the Anthropic model identifier (Twelve-Factor: from the environment)."""
    if load_env:
        load_dotenv()
    return os.environ.get(MODEL_ENV) or DEFAULT_MODEL


def get_anthropic_api_key(load_env: bool = True) -> str:
    """Return the Anthropic API key; raise ``ConfigError`` if it is not set."""
    if load_env:
        load_dotenv()
    key = os.environ.get(API_KEY_ENV)
    if not key:
        raise ConfigError(
            f"{API_KEY_ENV} is not set. Add it to your .env to run engine commands."
        )
    return key


def get_default_language(load_env: bool = True) -> str:
    """Return the default output/analysis language (ISO 639-1)."""
    if load_env:
        load_dotenv()
    return os.environ.get(LANGUAGE_ENV) or DEFAULT_LANGUAGE


def get_provider(load_env: bool = True) -> str:
    """Return the configured LLM provider (``anthropic`` or ``openai``)."""
    if load_env:
        load_dotenv()
    provider = (os.environ.get(PROVIDER_ENV) or DEFAULT_PROVIDER).lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ConfigError(
            f"{PROVIDER_ENV}={provider!r} is not supported; "
            f"choose one of {', '.join(SUPPORTED_PROVIDERS)}."
        )
    return provider


def get_openai_api_key(load_env: bool = True) -> str:
    """Return the OpenAI API key; raise ``ConfigError`` if it is not set."""
    if load_env:
        load_dotenv()
    key = os.environ.get(OPENAI_API_KEY_ENV)
    if not key:
        raise ConfigError(
            f"{OPENAI_API_KEY_ENV} is not set. Add it to your .env to use the "
            "OpenAI provider."
        )
    return key


def get_openai_model(load_env: bool = True) -> str:
    """Return the OpenAI model; raise ``ConfigError`` if it is not set.

    There is no default: the chosen model must support structured outputs, so the
    user picks it explicitly.
    """
    if load_env:
        load_dotenv()
    model = os.environ.get(OPENAI_MODEL_ENV)
    if not model:
        raise ConfigError(
            f"{OPENAI_MODEL_ENV} is not set. Set it in your .env to a model that "
            "supports structured outputs (e.g. a current gpt-4o/gpt-4.1-class model)."
        )
    return model


def get_followup_days(load_env: bool = True) -> int:
    """Return the number of days after applying before a follow-up is due."""
    if load_env:
        load_dotenv()
    raw = os.environ.get(FOLLOWUP_DAYS_ENV)
    if not raw:
        return DEFAULT_FOLLOWUP_DAYS
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"{FOLLOWUP_DAYS_ENV} must be an integer, got {raw!r}"
        ) from exc
