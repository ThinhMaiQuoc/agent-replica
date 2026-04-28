from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class ZendeskArticle:
    article_id: int
    title: str
    html_url: str
    body_html: str
    updated_at: str | None
    edited_at: str | None
    locale: str


def fetch_articles(base_url: str, locale: str, limit: int, timeout_seconds: int = 30) -> list[ZendeskArticle]:
    endpoint = f"{base_url.rstrip('/')}/api/v2/help_center/{locale}/articles.json"
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "agent-replica/1.0",
        }
    )

    articles: list[ZendeskArticle] = []
    per_page = min(max(limit, 1), 100)
    next_page: str | None = endpoint
    params: dict[str, int] | None = {"per_page": per_page}

    while next_page and len(articles) < limit:
        response = session.get(
            next_page,
            params=params,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        params = None
        batch = payload.get("articles", [])
        if not batch:
            break

        for item in batch:
            if item.get("draft"):
                continue
            body_html = (item.get("body") or "").strip()
            title = (item.get("title") or "").strip()
            html_url = (item.get("html_url") or "").strip()
            if not body_html or not title or not html_url:
                continue

            articles.append(
                ZendeskArticle(
                    article_id=int(item["id"]),
                    title=title,
                    html_url=html_url,
                    body_html=body_html,
                    updated_at=item.get("updated_at"),
                    edited_at=item.get("edited_at"),
                    locale=item.get("locale") or locale,
                )
            )
            if len(articles) >= limit:
                break

        next_page = payload.get("next_page")

    return sorted(articles[:limit], key=lambda article: article.article_id)
