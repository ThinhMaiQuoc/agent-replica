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
    zendesk_base_url: str
    zendesk_locale: str
    docs_dir: Path
    manifest_path: Path


def load_config(argv: list[str] | None = None) -> Config:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Fetch OptiSigns support articles and write normalized Markdown files."
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
    args = parser.parse_args(argv)
    article_limit = args.article_limit if args.article_limit is not None else _get_int_env("ARTICLE_LIMIT", 30)

    config = Config(
        dry_run=args.dry_run,
        article_limit=article_limit,
        zendesk_base_url=os.getenv("ZENDESK_BASE_URL", "https://support.optisigns.com").rstrip("/"),
        zendesk_locale=os.getenv("ZENDESK_LOCALE", "en-us"),
        docs_dir=Path(os.getenv("DOCS_DIR", "docs")),
        manifest_path=Path(os.getenv("MANIFEST_PATH", "state/manifest.json")),
    )

    validate_config(config)
    return config


def validate_config(config: Config) -> None:
    if config.article_limit <= 0:
        raise ConfigError("ARTICLE_LIMIT must be a positive integer.")


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer.") from exc
