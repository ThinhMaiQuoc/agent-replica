# agent-replica Plan

## Current State
- Previous scaffold was removed.
- Rebuild started from a clean repo with a new git init.
- Base directories exist: `app/`, `docs/`, `state/`, `screenshots/`.

## Done
- Review Gate 1 complete: reset confirmed.
- Review Gate 2 complete: project skeleton and tracking files created.
- Architecture decisions locked for the rebuild.
- Review Gate 3 complete: CLI entrypoint and config validation are in place.
- Review Gate 4 complete: Zendesk fetch and Markdown normalization are wired into the run path.
- Review Gate 5 complete: OpenAI vector-store sync and optional assistant attach are wired into the run path.

## Next
- Review Gate 6: add manifest logging, Docker/README polish, and DigitalOcean delivery cleanup.
- Dry-run still writes real Markdown article files under `docs/`.
- Production remains strict: plain `python main.py` must require `OPENAI_VECTOR_STORE_ID`.

## Decisions Locked
- Full wipe and clean rebuild.
- Compact `app/` layout.
- OpenAI vector-store file attributes are the production delta source of truth.
- `state/manifest.json` is a local debug mirror only.
- Assistant is created manually in Playground, with only optional helper support in code.
- Exact chunk counting is best-effort; fallback must be logged as `estimated_chunks`.
- Vector store creation must be explicit via bootstrap flag.

## Acceptance Checklist
- Scrape and normalize at least 30 support articles into Markdown files.
- Delta sync works for added, updated, and unchanged articles.
- Docker run executes one sync and exits `0`.
- README is concise and complete.
- Screenshot placeholder exists for Playground proof.
- DigitalOcean scheduled job config is present.

## Notes / What Happened
- Initial scaffold was intentionally discarded.
- The rebuild is now happening in gated steps so each stage can be reviewed before moving on.
- Config was simplified so the current phase only covers scrape settings: article limit, Zendesk target, output path, and dry-run behavior.
- The scraper now pulls public Zendesk articles and writes normalized Markdown files with metadata and article URLs.
- The sync path now uploads Markdown files into one OpenAI vector store, tracks deltas via file attributes, and can optionally attach that store to a Playground assistant.
