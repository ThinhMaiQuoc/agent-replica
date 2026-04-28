from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as to_markdown

from app.zendesk import ZendeskArticle


@dataclass(frozen=True)
class RenderedArticle:
    article_id: int
    title: str
    slug: str
    url: str
    updated_at: str | None
    edited_at: str | None
    article_hash: str
    markdown_body: str
    document: str
    output_path: Path


def render_articles(articles: list[ZendeskArticle], docs_dir: Path, base_url: str) -> list[RenderedArticle]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    rendered_articles: list[RenderedArticle] = []

    for article in articles:
        rendered = render_article(article, docs_dir=docs_dir, base_url=base_url)
        rendered.output_path.write_text(rendered.document, encoding="utf-8")
        rendered_articles.append(rendered)

    return rendered_articles


def render_article(article: ZendeskArticle, docs_dir: Path, base_url: str) -> RenderedArticle:
    cleaned_html = _clean_html(article.body_html)
    soup = BeautifulSoup(cleaned_html, "html.parser")
    _rewrite_internal_links(soup, base_url)

    markdown_body = _normalize_markdown(
        to_markdown(
            str(soup),
            heading_style="ATX",
            bullets="-",
            wrap=False,
            strong_em_symbol="*",
        )
    )
    slug = slugify(article.title)
    article_hash = compute_article_hash(
        article_id=article.article_id,
        title=article.title,
        url=article.html_url,
        updated_at=article.updated_at,
        edited_at=article.edited_at,
        markdown_body=markdown_body,
    )
    output_path = docs_dir / f"{article.article_id}-{slug}.md"
    document = build_markdown_document(
        article_id=article.article_id,
        title=article.title,
        url=article.html_url,
        updated_at=article.updated_at,
        edited_at=article.edited_at,
        article_hash=article_hash,
        markdown_body=markdown_body,
    )

    return RenderedArticle(
        article_id=article.article_id,
        title=article.title,
        slug=slug,
        url=article.html_url,
        updated_at=article.updated_at,
        edited_at=article.edited_at,
        article_hash=article_hash,
        markdown_body=markdown_body,
        document=document,
        output_path=output_path,
    )


def build_markdown_document(
    article_id: int,
    title: str,
    url: str,
    updated_at: str | None,
    edited_at: str | None,
    article_hash: str,
    markdown_body: str,
) -> str:
    return "\n".join(
        [
            "---",
            f"article_id: {article_id}",
            f'title: "{_yaml_escape(title)}"',
            f'url: "{_yaml_escape(url)}"',
            f'updated_at: "{_yaml_escape(updated_at or "")}"',
            f'edited_at: "{_yaml_escape(edited_at or "")}"',
            f'article_hash: "{article_hash}"',
            "---",
            f"# {title}",
            "",
            f"Article URL: {url}",
            "",
            markdown_body,
            "",
        ]
    )


def compute_article_hash(
    article_id: int,
    title: str,
    url: str,
    updated_at: str | None,
    edited_at: str | None,
    markdown_body: str,
) -> str:
    payload = "\n".join(
        [
            str(article_id),
            title.strip(),
            url.strip(),
            updated_at or "",
            edited_at or "",
            markdown_body.strip(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    compact = re.sub(r"-{2,}", "-", cleaned)
    return compact or "article"


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("script,style,nav,header,footer,aside,form,noscript,iframe"):
        tag.decompose()
    return str(soup)


def _rewrite_internal_links(soup: BeautifulSoup, base_url: str) -> None:
    base_netloc = urlparse(base_url).netloc
    for link in soup.select("a[href]"):
        href = (link.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:")):
            continue
        parsed = urlparse(href)
        if not parsed.netloc:
            continue
        if parsed.netloc != base_netloc:
            continue

        relative_path = parsed.path or "/"
        if parsed.query:
            relative_path = f"{relative_path}?{parsed.query}"
        if parsed.fragment:
            relative_path = f"{relative_path}#{parsed.fragment}"
        link["href"] = relative_path


def _normalize_markdown(markdown_text: str) -> str:
    cleaned = markdown_text.replace("\r\n", "\n").strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def _yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
