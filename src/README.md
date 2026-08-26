# Source

The application package will live under `src/riverside_marketing/`.

Planned boundaries:

- `data/` — loading and validating catalog records.
- `generation/` — turning validated book inputs into deterministic drafts.
- `engagement.py` — validating reader context and selecting a deterministic next-best engagement message.
- `outputs/` — channel-specific draft representations and handoff formats.

The current implementation layers are:

- `data/validation.py` — loads the Product D book contract, validates individual records, loads JSON collections, and quarantines invalid entries.
- `generation/drafts.py` — creates deterministic promotional-description, social-media, and email-campaign drafts from validated records.
- `orchestration.py` — coordinates catalog loading, per-record validation, rejected-record diagnostics, and draft generation.
- `cli.py` and `__main__.py` — provide a local JSON CLI seam for running the catalog workflow.
- `api.py` — provides the v0.1 `/health` and `/generate` HTTP adapter over orchestration. `/generate` accepts the original catalog array or an object containing `catalog` and optional `reader_context`.

External AI generation, APIs, user interfaces, and publishing workflows are intentionally out of scope.

When reader context is supplied, orchestration still returns the original
catalog drafts and adds one structured `engagement_messages` result. Supported
context fields include `reader_id`, `favorite_genres`, `books_read`,
`active_challenge`, `challenge_progress`, `last_visit`, `community_progress`,
and `community_goal`.

Run the local CLI with:

```bash
PYTHONPATH=src python3 -m riverside_marketing data/fixtures/books.mixed.json
```

Run the local HTTP API with:

```bash
PYTHONPATH=src uvicorn riverside_marketing.api:app --reload
```
