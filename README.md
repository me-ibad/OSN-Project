# Bluesky COIN feasibility pilot

This folder is a reproducible pilot for the proposed project, **AI and the Future
of Software Development: Sentiment, Communities, and Interaction Networks on
Bluesky**.

## Contents

- `collect_bluesky_pilot.py` — paginated public-API collector.
- `bluesky_posts.csv` — pilot search sample (created when the collector runs).
- `collection_metadata.json` — query, timing, API request URLs, and counts.
- `PILOT_REPORT.md` — results and a recommended next step for the status meeting.

## Reproduce the pilot

Requires Python 3 and `requests` (`python3 -m pip install requests` if needed).

```bash
python3 collect_bluesky_pilot.py \
  --query 'AI software developers' --limit 100 --sort latest --output-dir .
```

The script uses the public endpoint
`app.bsky.feed.searchPosts`, handles pagination and duplicate post URIs, and
records the exact request URLs in the metadata file. Results are not exhaustive:
search coverage and availability can change.

## Ethical handling

Posts are public but can contain personal data. Keep the raw CSV access-limited,
avoid publishing handles or post text in reports, minimize retained data, and
document the sampling window and filtering decisions.
