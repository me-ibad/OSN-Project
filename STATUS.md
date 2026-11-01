# Pilot status — 31 October 2026

## Outcome

**Inconclusive: server access blocked in this environment.** The public Bluesky
search endpoint returned HTTP 403 Forbidden during a real read-only collection
attempt. A failure record is saved in `collection_failure.json`.

## What is complete

- Reproducible, paginated collector with URI deduplication.
- Data fields required for post, engagement, and reply-network analysis.
- Collection protocol, ethical guidance, and a meeting-ready pilot report.
- A recorded access-failure result instead of invented sample data.

## Next action

From a different network, run:

```bash
python3 collect_bluesky_pilot.py --query 'AI software developers' --limit 100 --sort latest --output-dir .
```

Then manually code relevance and stance for a random subset before deciding whether
to expand to the full sample.
