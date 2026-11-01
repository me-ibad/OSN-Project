#!/usr/bin/env python3
"""Test authenticated Bluesky search pagination without storing credentials."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from atproto import Client, models


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="AI software developers")
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--max-pages", type=int, default=2)
    args = parser.parse_args()
    handle = os.environ.get("BSKY_HANDLE")
    app_password = os.environ.get("BSKY_APP_PASSWORD")
    if not handle or not app_password:
        raise SystemExit(
            "Set BSKY_HANDLE and BSKY_APP_PASSWORD in this shell. "
            "Use a Bluesky app password, never your main password."
        )
    if not 1 <= args.page_size <= 100 or args.max_pages < 1:
        raise SystemExit("--page-size must be 1–100 and --max-pages must be positive.")

    client = Client()
    client.login(handle, app_password)
    cursor = None
    pages, unique_uris = [], set()
    for number in range(1, args.max_pages + 1):
        params = models.AppBskyFeedSearchPosts.Params(
            q=args.query, limit=args.page_size, sort="latest", cursor=cursor
        )
        try:
            response = client.app.bsky.feed.search_posts(params)
        except Exception as error:  # The SDK exposes several transport error classes.
            pages.append({"page": number, "success": False, "error": f"{type(error).__name__}: {error}"})
            break
        posts = list(response.posts or [])
        for post in posts:
            if post.uri:
                unique_uris.add(str(post.uri))
        cursor = response.cursor
        pages.append({
            "page": number, "success": True, "posts_returned": len(posts),
            "cursor_returned": bool(cursor), "used_cursor": number > 1,
        })
        if not cursor or not posts:
            break

    completed = bool(pages) and pages[-1]["success"] and not pages[-1].get("cursor_returned", False)
    page_limit_reached = bool(pages) and pages[-1]["success"] and pages[-1].get("cursor_returned", False) and len(pages) >= args.max_pages
    result = {
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "authenticated atproto Python client",
        "query": args.query, "page_size": args.page_size, "max_pages_requested": args.max_pages,
        "pages": pages, "unique_post_uris": len(unique_uris),
        "status": "completed" if completed else ("page_limit_reached" if page_limit_reached else ("partial_success" if unique_uris else "failed")),
        "credentials_stored": False,
    }
    Path("authenticated_search_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
