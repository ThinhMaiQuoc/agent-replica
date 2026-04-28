from __future__ import annotations

import logging

from app.config import ConfigError, load_config
from app.markdown import render_articles
from app.zendesk import fetch_articles


def main(argv: list[str] | None = None) -> int:
    try:
        config = load_config(argv)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    logging.basicConfig(level=logging.INFO)
    articles = fetch_articles(
        base_url=config.zendesk_base_url,
        locale=config.zendesk_locale,
        limit=config.article_limit,
    )
    rendered_articles = render_articles(
        articles=articles,
        docs_dir=config.docs_dir,
        base_url=config.zendesk_base_url,
    )
    logging.info(
        "Phase 2 checkpoint: fetched_articles=%s written_docs=%s docs_dir=%s dry_run=%s",
        len(articles),
        len(rendered_articles),
        config.docs_dir,
        config.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
