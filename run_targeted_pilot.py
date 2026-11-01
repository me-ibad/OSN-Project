#!/usr/bin/env python3
"""Run the five targeted Bluesky searches for the COIN feasibility pilot."""

from __future__ import annotations

import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
QUERIES = [
    "AI replacing programmers",
    "AI coding jobs",
    "AI software engineering",
    "GitHub Copilot developers",
    "AI impact on developers",
]
FIELDS = [
    "query", "uri", "author_did", "author_handle", "text", "created_at",
    "langs", "reply_parent_uri", "reply_root_uri", "reply_count", "repost_count",
    "like_count", "quote_count", "relevance", "stance", "review_notes",
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def collect(query: str, limit: int = 100) -> tuple[list[dict], list[dict]]:
    posts, requests_log, seen, cursor, page_number = [], [], set(), None, 0
    while len(posts) < limit:
        params = {"q": query, "limit": min(100, limit - len(posts)), "sort": "latest"}
        if cursor:
            params["cursor"] = cursor
        page_number += 1
        response = requests.get(
            API_URL, params=params, timeout=30,
            headers={"User-Agent": "COIN-Bluesky-Feasibility-Pilot/1.0"},
        )
        requests_log.append({"page": page_number, "url": response.url, "status_code": response.status_code, "used_cursor": bool(cursor), "content_type": response.headers.get("content-type"), "rate_limit_remaining": response.headers.get("ratelimit-remaining"), "request_id": response.headers.get("x-request-id")})
        # Preserve a successful first page if the API later rejects a cursor request.
        if response.status_code != 200:
            requests_log[-1]["error"] = response.text[:500]
            break
        payload = response.json()
        page = payload.get("posts", [])
        for post in page:
            if post.get("uri") in seen:
                continue
            seen.add(post.get("uri"))
            author, record, reply = post.get("author") or {}, post.get("record") or {}, (post.get("record") or {}).get("reply") or {}
            posts.append({
                "query": query, "uri": post.get("uri", ""),
                "author_did": author.get("did", ""), "author_handle": author.get("handle", ""),
                "text": record.get("text", ""), "created_at": record.get("createdAt", ""),
                "langs": ",".join(post.get("langs") or []),
                "reply_parent_uri": (reply.get("parent") or {}).get("uri", ""),
                "reply_root_uri": (reply.get("root") or {}).get("uri", ""),
                "reply_count": post.get("replyCount", 0), "repost_count": post.get("repostCount", 0),
                "like_count": post.get("likeCount", 0), "quote_count": post.get("quoteCount", 0),
                "relevance": "", "stance": "", "review_notes": "",
            })
        requests_log[-1]["posts_in_page"] = len(page)
        cursor = payload.get("cursor")
        requests_log[-1]["cursor_returned"] = bool(cursor)
        if not page or not cursor:
            break
        time.sleep(0.25)
    return posts[:limit], requests_log


def main() -> None:
    output_dir = Path(".")
    started = datetime.now(timezone.utc)
    run = {"started_at_utc": started.isoformat(), "endpoint": API_URL, "queries": []}
    all_posts = []
    for query in QUERIES:
        posts, requests_log = collect(query)
        filename = f"pilot_{slug(query)}.csv"
        with (output_dir / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(posts)
        run["queries"].append({
            "query": query, "returned_posts": len(posts), "file": filename,
            "pages_successful": sum(1 for entry in requests_log if entry["status_code"] == 200),
            "pagination_complete": bool(requests_log) and requests_log[-1].get("status_code") == 200 and not requests_log[-1].get("cursor_returned", False),
            "status": "completed" if requests_log and requests_log[-1].get("status_code") == 200 and not requests_log[-1].get("cursor_returned", False) else "partial_success",
            "pagination_error": next(("HTTP " + str(entry["status_code"]) + " " + entry.get("error", "") for entry in requests_log if entry["status_code"] != 200), None),
            "requests": requests_log,
        })
        all_posts.extend(posts)
    unique_uris = len({post["uri"] for post in all_posts})
    run["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    run["total_returned_posts"] = len(all_posts)
    run["unique_post_uris_across_queries"] = unique_uris
    (output_dir / "targeted_pilot_metadata.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    with (output_dir / "targeted_pilot_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["query", "returned_posts", "file"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(run["queries"])
    print(json.dumps(run, indent=2))


if __name__ == "__main__":
    main()
