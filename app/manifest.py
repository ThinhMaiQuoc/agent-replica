from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.markdown import RenderedArticle


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(
    *,
    dry_run: bool,
    vector_store_id: str | None,
    zendesk_base_url: str,
    zendesk_locale: str,
    article_limit: int,
    fetched_articles: int,
    written_docs: int,
    counts: dict[str, int],
    rendered_articles: list[RenderedArticle],
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "vector_store_id": vector_store_id,
        "zendesk": {
            "base_url": zendesk_base_url,
            "locale": zendesk_locale,
            "article_limit": article_limit,
        },
        "counts": {
            "fetched_articles": fetched_articles,
            "written_docs": written_docs,
            "added": counts.get("added", 0),
            "updated": counts.get("updated", 0),
            "skipped": counts.get("skipped", 0),
            "uploaded_files": counts.get("uploaded_files", 0),
            "embedded_chunks": counts.get("embedded_chunks", 0),
            "estimated_chunks": counts.get("estimated_chunks", 0),
        },
        "articles": [_render_article_entry(article) for article in rendered_articles],
    }


def _render_article_entry(article: RenderedArticle) -> dict[str, Any]:
    return {
        "article_id": article.article_id,
        "slug": article.slug,
        "article_hash": article.article_hash,
        "url": article.url,
        "updated_at": article.updated_at,
        "output_path": str(article.output_path),
    }