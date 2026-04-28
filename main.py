from __future__ import annotations

import logging

from app.config import ConfigError, load_config
from app.markdown import render_articles
from app.openai_store import (
    attach_vector_store_to_assistant,
    bootstrap_vector_store,
    create_client,
    sync_rendered_articles,
)
from app.zendesk import fetch_articles


def main(argv: list[str] | None = None) -> int:
    try:
        config = load_config(argv)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    logging.basicConfig(level=logging.INFO)
    try:
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
            "Scrape complete: fetched_articles=%s written_docs=%s docs_dir=%s dry_run=%s",
            len(articles),
            len(rendered_articles),
            config.docs_dir,
            config.dry_run,
        )

        if config.dry_run:
            return 0

        client = create_client(config.openai_api_key or "")
        vector_store_id = config.openai_vector_store_id
        if not vector_store_id and config.bootstrap_vector_store:
            vector_store_id = bootstrap_vector_store(
                client=client,
                name=config.openai_vector_store_name,
                description=config.openai_vector_store_description,
            )
            logging.info("Created vector store: %s", vector_store_id)

        if not vector_store_id:
            raise RuntimeError("OPENAI_VECTOR_STORE_ID is required for non-dry-run sync.")

        sync_result = sync_rendered_articles(
            client=client,
            vector_store_id=vector_store_id,
            rendered_articles=rendered_articles,
        )
        if config.attach_assistant and config.openai_assistant_id:
            attach_vector_store_to_assistant(
                client=client,
                assistant_id=config.openai_assistant_id,
                vector_store_id=vector_store_id,
            )
            logging.info("Attached vector store %s to assistant %s", vector_store_id, config.openai_assistant_id)

        logging.info(
            "Phase 3 checkpoint: vector_store_id=%s added=%s updated=%s skipped=%s uploaded_files=%s "
            "embedded_chunks=%s estimated_chunks=%s",
            vector_store_id,
            sync_result.added,
            sync_result.updated,
            sync_result.skipped,
            sync_result.uploaded_files,
            sync_result.embedded_chunks,
            sync_result.estimated_chunks,
        )
        return 0
    except Exception:
        logging.exception("Sync run failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
