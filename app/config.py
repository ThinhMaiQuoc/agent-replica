from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    dry_run: bool
    article_limit: int
    bootstrap_vector_store: bool
    attach_assistant: bool
    zendesk_base_url: str
    zendesk_locale: str
    docs_dir: Path
    manifest_path: Path
    openai_api_key: str | None
    openai_vector_store_id: str | None
    openai_assistant_id: str | None
    openai_vector_store_name: str
    openai_vector_store_description: str


def load_config(argv: list[str] | None = None) -> Config:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Fetch OptiSigns support articles, write normalized Markdown, and optionally sync to OpenAI."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the scrape pipeline without later OpenAI sync steps.",
    )
    parser.add_argument(
        "--article-limit",
        type=int,
        help="Number of articles to fetch for this run. Defaults to ARTICLE_LIMIT or 30.",
    )
    parser.add_argument(
        "--bootstrap-vector-store",
        action="store_true",
        help="Create a vector store for local first-run setup when OPENAI_VECTOR_STORE_ID is missing.",
    )
    parser.add_argument(
        "--attach-assistant",
        action="store_true",
        help="Attach the vector store to OPENAI_ASSISTANT_ID after sync.",
    )
    args = parser.parse_args(argv)
    article_limit = args.article_limit if args.article_limit is not None else _get_int_env("ARTICLE_LIMIT", 30)

    config = Config(
        dry_run=args.dry_run,
        article_limit=article_limit,
        bootstrap_vector_store=args.bootstrap_vector_store,
        attach_assistant=args.attach_assistant,
        zendesk_base_url=os.getenv("ZENDESK_BASE_URL", "https://support.optisigns.com").rstrip("/"),
        zendesk_locale=os.getenv("ZENDESK_LOCALE", "en-us"),
        docs_dir=Path(os.getenv("DOCS_DIR", "docs")),
        manifest_path=Path(os.getenv("MANIFEST_PATH", "state/manifest.json")),
        openai_api_key=_get_optional_env("OPENAI_API_KEY"),
        openai_vector_store_id=_get_optional_env("OPENAI_VECTOR_STORE_ID"),
        openai_assistant_id=_get_optional_env("OPENAI_ASSISTANT_ID"),
        openai_vector_store_name=os.getenv("OPENAI_VECTOR_STORE_NAME", "signal-cache-kb").strip(),
        openai_vector_store_description=os.getenv(
            "OPENAI_VECTOR_STORE_DESCRIPTION", "OptiBot support knowledge base"
        ).strip(),
    )

    validate_config(config)
    return config


def validate_config(config: Config) -> None:
    if config.article_limit <= 0:
        raise ConfigError("ARTICLE_LIMIT must be a positive integer.")

    if config.attach_assistant and not config.openai_assistant_id:
        raise ConfigError("--attach-assistant requires OPENAI_ASSISTANT_ID.")

    if config.dry_run:
        return

    if not config.openai_api_key:
        raise ConfigError("OPENAI_API_KEY is required unless --dry-run is used.")

    if not config.openai_vector_store_id and not config.bootstrap_vector_store:
        raise ConfigError(
            "OPENAI_VECTOR_STORE_ID is required for sync runs. "
            "Use --bootstrap-vector-store only for local first-run setup."
        )


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer.") from exc


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
