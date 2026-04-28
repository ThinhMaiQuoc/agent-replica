# agent-replica

Small scheduled ingestion job for an OptiBot-style support assistant.

## Current Behavior
- Fetch public OptiSigns Help Center articles from Zendesk.
- Convert article HTML to clean Markdown files in `docs/`.
- Sync only new or changed docs to one OpenAI vector store.
- Use vector-store file attributes as the production delta source of truth.

## Commands
```bash
python main.py --dry-run
python main.py --bootstrap-vector-store
python main.py
python main.py --attach-assistant
docker build -t agent-replica .
docker run --rm --env-file .env agent-replica
```

## Chunk Strategy
- Each support article is saved as one Markdown file and uploaded to OpenAI as one file.
- The app does not split articles into chunks itself. OpenAI vector stores handle that automatically using the default `auto` chunking strategy. Per current OpenAI docs, this means up to 800 tokens per chunk with 400-token overlap.
- After upload, the job tries to count the parsed chunks returned by OpenAI and logs them as `embedded_chunks`. If the API does not expose that clearly, the job logs `estimated_chunks` instead. The estimate uses `ceil(len(text) / 4)` as a rough token count.

## Deliverables
- Screenshot placeholder path: `screenshots/playground-answer.png`
- DigitalOcean logs URL: add after deployment
