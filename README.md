# agent-replica

Small scheduled ingestion job for an OptiBot-style support assistant.

## Status
- Review Gate 2 complete: project skeleton created.
- App logic is not implemented yet in this step.

## Planned Behavior
- Fetch public OptiSigns Help Center articles from Zendesk.
- Convert article HTML to clean Markdown files in `docs/`.
- Sync only new or changed docs to one OpenAI vector store.
- Use vector-store file attributes as the production delta source of truth.

## Planned Commands
```bash
python main.py --dry-run
python main.py --bootstrap-vector-store
docker build -t agent-replica .
docker run --rm --env-file .env agent-replica
```

## Deliverables
- Screenshot placeholder path: `screenshots/playground-answer.png`
- DigitalOcean logs URL: add after deployment

Implementation details and setup instructions will be filled in during later review gates.
