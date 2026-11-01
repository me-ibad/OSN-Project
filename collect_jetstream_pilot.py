#!/usr/bin/env python3
"""Bounded Jetstream feasibility collector for AI and software-work discussions."""

from __future__ import annotations

import argparse
import csv
import json
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import websocket

URL = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
FIELDS = [
    "uri", "author_did", "text", "created_at", "event_time_us", "langs",
    "reply_parent_uri", "reply_root_uri", "collection_status",
]
AI_TERMS = re.compile(r"\b(ai|artificial intelligence|llm|large language model|chatgpt|copilot|claude|gemini|cursor)\b", re.I)
SOFTWARE_TERMS = re.compile(r"\b(developer|developers|programmer|programmers|programming|code|coding|software|engineer|engineering|job|jobs|career|careers)\b", re.I)


class Collector:
    def __init__(self, duration_seconds: int, target_relevant: int) -> None:
        self.duration_seconds = duration_seconds
        self.target_relevant = target_relevant
        self.started = datetime.now(timezone.utc)
        self.deadline = time.monotonic() + duration_seconds
        self.seen, self.rows = set(), {}
        self.total_messages = self.post_creates = self.relevant_posts = self.reply_relationships = self.deletions = 0
        self.errors: list[str] = []
        self.connection_opened = False
        self.status = "running"
        self.ws = None

    def snapshot(self, final: bool = False) -> None:
        status = {
            "started_at_utc": self.started.isoformat(),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "endpoint": URL,
            "collection_duration_target_seconds": self.duration_seconds,
            "target_relevant_posts": self.target_relevant,
            "connection_opened": self.connection_opened,
            "status": self.status,
            "total_events_observed": self.total_messages,
            "post_create_events": self.post_creates,
            "relevant_posts": self.relevant_posts,
            "reply_relationships": self.reply_relationships,
            "deletion_events_for_retained_posts": self.deletions,
            "unique_retained_posts": len(self.rows),
            "errors": self.errors,
        }
        if final:
            status["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        Path("jetstream_collection_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
        with Path("jetstream_relevant_posts.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.rows.values())

    def should_keep(self, text: str) -> bool:
        return bool(AI_TERMS.search(text) and SOFTWARE_TERMS.search(text))

    def on_open(self, ws) -> None:
        self.connection_opened = True
        self.snapshot()
        print("Jetstream collection started", flush=True)

    def on_message(self, ws, message: str) -> None:
        self.total_messages += 1
        try:
            event = json.loads(message)
        except json.JSONDecodeError as error:
            self.errors.append(f"Invalid JSON: {error}")
            return
        if event.get("kind") != "commit":
            return
        commit = event.get("commit") or {}
        did, rkey = event.get("did", ""), commit.get("rkey", "")
        uri = f"at://{did}/app.bsky.feed.post/{rkey}" if did and rkey else ""
        operation = commit.get("operation")
        if operation == "delete" and uri in self.rows:
            self.rows[uri]["collection_status"] = "deleted"
            self.deletions += 1
            return
        if operation != "create":
            return
        self.post_creates += 1
        record = commit.get("record") or {}
        text = record.get("text", "")
        if not text or not self.should_keep(text) or uri in self.seen:
            return
        self.seen.add(uri)
        reply = record.get("reply") or {}
        parent = (reply.get("parent") or {}).get("uri", "")
        root = (reply.get("root") or {}).get("uri", "")
        self.rows[uri] = {
            "uri": uri, "author_did": did, "text": text,
            "created_at": record.get("createdAt", ""), "event_time_us": event.get("time_us", ""),
            "langs": ",".join(record.get("langs") or []),
            "reply_parent_uri": parent, "reply_root_uri": root, "collection_status": "active",
        }
        self.relevant_posts += 1
        if parent:
            self.reply_relationships += 1
        if self.relevant_posts % 10 == 0:
            print(f"Relevant posts: {self.relevant_posts}; replies: {self.reply_relationships}", flush=True)
            self.snapshot()
        if self.relevant_posts >= self.target_relevant:
            self.status = "success_target_reached"
            ws.close()

    def on_error(self, ws, error) -> None:
        self.errors.append(str(error))
        print("Jetstream error:", error, flush=True)

    def on_close(self, ws, code, reason) -> None:
        if self.status == "running":
            self.status = "partial_success" if self.relevant_posts else "failed"
        self.snapshot(final=True)
        print(f"Jetstream collection closed: {code} {reason}", flush=True)

    def run(self) -> None:
        def close_at_deadline() -> None:
            if self.ws:
                self.ws.close()
        timer = threading.Timer(self.duration_seconds, close_at_deadline)
        timer.start()
        try:
            self.ws = websocket.WebSocketApp(URL, on_open=self.on_open, on_message=self.on_message,
                                             on_error=self.on_error, on_close=self.on_close)
            self.ws.run_forever(ping_interval=30, ping_timeout=10)
        finally:
            timer.cancel()
            self.snapshot(final=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-minutes", type=float, default=30)
    parser.add_argument("--target-relevant", type=int, default=50)
    args = parser.parse_args()
    Collector(int(args.duration_minutes * 60), args.target_relevant).run()


if __name__ == "__main__":
    main()
