# agent-replica

Scheduled ingestion job for an OptiBot-style support assistant using OptiSigns support articles and an OpenAI vector store.

## Project Status

- The scrape-to-Markdown path is locally verified.
- The local dry-run path can be executed without OpenAI billing and writes normalized Markdown files to `docs/`.
- The vector-store sync implementation is present in code.
- Live OpenAI vector-store, Assistant, and DigitalOcean verification is deferred because billing is not enabled in the current account.
- `screenshots/playground-answer.png` and the deployed logs URL are TODO placeholders, not completed proof artifacts.

## Env Vars

- Required for real sync: `OPENAI_API_KEY`, `OPENAI_VECTOR_STORE_ID`
- Optional: `OPENAI_ASSISTANT_ID`, `OPENAI_VECTOR_STORE_NAME`, `OPENAI_VECTOR_STORE_DESCRIPTION`, `ZENDESK_BASE_URL`, `ZENDESK_LOCALE`, `ARTICLE_LIMIT`

## Local Commands

```bash
# Free/local verification path
python main.py --dry-run

# Requires OpenAI Platform billing/API access
python main.py --bootstrap-vector-store
python main.py
python main.py --attach-assistant

## Chunk Strategy
- Each article is uploaded as one file.
- The app relies on OpenAI vector store auto chunking rather than pre-chunking locally.
- embedded_chunks means parsed content items were observable after upload.
- estimated_chunks is the fallback estimate using ceil(len(text) / 4) with the documented 800-token chunks and 400-token overlap assumption.

## Docker Run
docker build -t agent-replica .
docker run --rm --env-file .env agent-replica

## DigitalOcean Job
- Production should run plain python main.py.
- OPENAI_VECTOR_STORE_ID is required in production; do not use --bootstrap-vector-store in the scheduled job path.

## TODO
- Screenshot path: screenshots/playground-answer.png
- Deployed DigitalOcean logs URL: TODO after live deployment