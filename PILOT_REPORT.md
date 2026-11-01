# Bluesky data-access feasibility pilot

## Aim

Test whether the public Bluesky API can retrieve a small, reproducible sample of
posts relevant to AI, programming jobs, and software development.

## Protocol

The collector runs a keyword search against Bluesky's public
`app.bsky.feed.searchPosts` endpoint. It requests up to 100 latest posts for the
query `AI software developers`, paginates where a cursor is returned, deduplicates
by post URI, and saves post text, timestamps, author identifiers, reply references,
and public engagement counts. The exact collection time and request URLs are stored
in `collection_metadata.json`.

## What the pilot tests

1. Public API accessibility and a successful response.
2. Presence of enough candidate posts to manually assess relevance.
3. Availability of reply-parent references needed for an interaction network.

## Pilot run: 31 October 2026

The collector was executed with the stated query and a target of 100 posts. The
public API host resolved when network access was permitted, but the server returned
**HTTP 403 Forbidden** to the `searchPosts` request. Consequently, no post CSV was
created in this environment. The saved `collection_failure.json` records the
timestamp, query, endpoint, and error verbatim. This is a useful pilot finding: the
claim that public reads need no API key does not guarantee access from every network
or execution environment.

The project should retry the identical command from a university or personal
network. Do not report that the team has collected Bluesky posts until it produces a
successful CSV and the metadata file records the retrieved count.

## How to interpret results

The CSV is a discovery sample, not a representative or complete historical sample.
Manually code a random subset as relevant / irrelevant and record whether each
relevant post expresses an optimistic, concerned, mixed, or unclear stance on AI's
effects on software work. A reply link represents interaction, not agreement.

## Decision rule

Proceed to the full collection only if the API works consistently, a meaningful
share of posts is relevant after manual review, and enough reply relationships are
available to build a network. Otherwise refine the keywords and consider prospective
Jetstream collection.

## Recommended status-meeting demonstration

Show the CSV, metadata, and one small network diagram constructed from the
`author_did`, `reply_parent_uri`, and `reply_root_uri` fields. State explicitly that
the pilot establishes feasibility, not prevalence or causal conclusions.
