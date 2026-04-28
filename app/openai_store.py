from __future__ import annotations

import logging
from dataclasses import dataclass
from math import ceil
from typing import Any

from openai import OpenAI

from app.markdown import RenderedArticle


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoteVectorStoreFile:
    file_id: str
    article_id: str | None
    article_hash: str | None
    attributes: dict[str, Any]
    status: str | None
    created_at: int | None


@dataclass(frozen=True)
class SyncResult:
    added: int
    updated: int
    skipped: int
    uploaded_files: int
    embedded_chunks: int
    estimated_chunks: int


def create_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def bootstrap_vector_store(client: OpenAI, name: str, description: str) -> str:
    vector_store = client.vector_stores.create(name=name, description=description)
    return vector_store.id


def list_vector_store_files(client: OpenAI, vector_store_id: str) -> list[RemoteVectorStoreFile]:
    remote_files: list[RemoteVectorStoreFile] = []
    page = client.vector_stores.files.list(vector_store_id=vector_store_id, limit=100)

    while True:
        for item in page.data:
            attributes = _coerce_mapping(getattr(item, "attributes", None))
            remote_files.append(
                RemoteVectorStoreFile(
                    file_id=item.id,
                    article_id=_as_optional_string(attributes.get("article_id")),
                    article_hash=_as_optional_string(attributes.get("article_hash")),
                    attributes=attributes,
                    status=getattr(item, "status", None),
                    created_at=getattr(item, "created_at", None),
                )
            )
        if not page.has_next_page():
            break
        page = page.get_next_page()

    return remote_files


def sync_rendered_articles(
    client: OpenAI,
    vector_store_id: str,
    rendered_articles: list[RenderedArticle],
) -> SyncResult:
    remote_index = _build_remote_index(list_vector_store_files(client, vector_store_id))

    added = 0
    updated = 0
    skipped = 0
    uploaded_files = 0
    embedded_chunks = 0
    estimated_chunks = 0

    for article in rendered_articles:
        remote_file = remote_index.get(str(article.article_id))
        if remote_file and remote_file.article_hash == article.article_hash and remote_file.status == "completed":
            skipped += 1
            continue

        if remote_file:
            updated += 1
            _delete_remote_file(client, vector_store_id, remote_file.file_id)
        else:
            added += 1

        uploaded_file_id = _upload_rendered_article(client, vector_store_id, article)
        uploaded_files += 1

        chunk_count = _count_remote_chunks(client, vector_store_id, uploaded_file_id)
        if chunk_count is None:
            estimated_chunks += _estimate_chunk_count(article.document)
        else:
            embedded_chunks += chunk_count

    return SyncResult(
        added=added,
        updated=updated,
        skipped=skipped,
        uploaded_files=uploaded_files,
        embedded_chunks=embedded_chunks,
        estimated_chunks=estimated_chunks,
    )


def attach_vector_store_to_assistant(client: OpenAI, assistant_id: str, vector_store_id: str) -> None:
    assistant = client.beta.assistants.retrieve(assistant_id)
    tools = [_to_dict(tool) for tool in getattr(assistant, "tools", []) or []]
    if not any(tool.get("type") == "file_search" for tool in tools):
        tools.append({"type": "file_search"})

    tool_resources = _to_dict(getattr(assistant, "tool_resources", None))
    file_search_resources = tool_resources.get("file_search")
    if not isinstance(file_search_resources, dict):
        file_search_resources = {}
    file_search_resources["vector_store_ids"] = [vector_store_id]
    tool_resources["file_search"] = file_search_resources

    client.beta.assistants.update(
        assistant_id,
        tools=tools,
        tool_resources=tool_resources,
    )


def _build_remote_index(remote_files: list[RemoteVectorStoreFile]) -> dict[str, RemoteVectorStoreFile]:
    remote_index: dict[str, RemoteVectorStoreFile] = {}
    sorted_files = sorted(remote_files, key=lambda item: item.created_at or 0, reverse=True)

    for remote_file in sorted_files:
        if not remote_file.article_id:
            continue
        if remote_file.article_id in remote_index:
            LOGGER.warning("Duplicate remote article_id detected: %s", remote_file.article_id)
            continue
        remote_index[remote_file.article_id] = remote_file

    return remote_index


def _upload_rendered_article(client: OpenAI, vector_store_id: str, article: RenderedArticle) -> str:
    with article.output_path.open("rb") as handle:
        uploaded_file = client.files.create(file=handle, purpose="assistants")

    vector_store_file = client.vector_stores.files.create_and_poll(
        vector_store_id=vector_store_id,
        file_id=uploaded_file.id,
        attributes=_build_file_attributes(article),
    )
    if getattr(vector_store_file, "status", None) != "completed":
        raise RuntimeError(f"Vector store file upload did not complete for article {article.article_id}.")
    return vector_store_file.id


def _delete_remote_file(client: OpenAI, vector_store_id: str, file_id: str) -> None:
    try:
        client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)
    except Exception:
        LOGGER.warning("Failed to delete vector store file %s", file_id, exc_info=True)

    try:
        client.files.delete(file_id)
    except Exception:
        LOGGER.warning("Failed to delete underlying OpenAI file %s", file_id, exc_info=True)


def _count_remote_chunks(client: OpenAI, vector_store_id: str, file_id: str) -> int | None:
    try:
        content_response = client.vector_stores.files.content(vector_store_id=vector_store_id, file_id=file_id)
    except Exception:
        LOGGER.warning("Unable to retrieve parsed vector store content for %s", file_id, exc_info=True)
        return None

    items = _extract_content_items(content_response)
    if items is None:
        return None
    return len(items)


def _extract_content_items(content_response: Any) -> list[Any] | None:
    if isinstance(content_response, dict):
        content = content_response.get("content")
        if isinstance(content, list):
            return content
        data = content_response.get("data")
        if isinstance(data, list):
            return data

    if hasattr(content_response, "content") and isinstance(content_response.content, list):
        return list(content_response.content)

    if hasattr(content_response, "data") and isinstance(content_response.data, list):
        return list(content_response.data)

    if hasattr(content_response, "to_dict"):
        payload = content_response.to_dict()
        return _extract_content_items(payload)

    return None


def _estimate_chunk_count(document_text: str) -> int:
    estimated_tokens = ceil(len(document_text) / 4)
    if estimated_tokens <= 0:
        return 0
    if estimated_tokens <= 800:
        return 1
    return 1 + ceil((estimated_tokens - 800) / 400)


def _build_file_attributes(article: RenderedArticle) -> dict[str, str]:
    return {
        "source": "zendesk",
        "article_id": str(article.article_id),
        "article_hash": article.article_hash,
        "slug": article.slug,
        "article_url": article.url,
        "updated_at": article.updated_at or "",
    }


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(exclude_none=True)
        if isinstance(dumped, dict):
            return dict(dumped)
    return {}


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(exclude_none=True)
        if isinstance(dumped, dict):
            return dict(dumped)
    if hasattr(value, "to_dict"):
        dumped = value.to_dict()
        if isinstance(dumped, dict):
            return dict(dumped)
    return {}


def _as_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
