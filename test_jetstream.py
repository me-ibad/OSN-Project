#!/usr/bin/env python3
"""Bounded connectivity test for Bluesky Jetstream public post events."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import websocket

URL = (
    "wss://jetstream2.us-east.bsky.network/subscribe"
    "?wantedCollections=app.bsky.feed.post"
)
TARGET_EVENTS = 20
TIMEOUT_SECONDS = 60
count = 0
result = {
    "endpoint": URL,
    "started_at_utc": datetime.now(timezone.utc).isoformat(),
    "connection_opened": False,
    "post_events_received": 0,
    "status": "running",
    "errors": [],
}


def save_result() -> None:
    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["post_events_received"] = count
    Path("jetstream_connectivity_result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )


def on_open(ws):
    result["connection_opened"] = True
    print("Jetstream connection opened")


def on_message(ws, message):
    global count
    try:
        event = json.loads(message)
    except json.JSONDecodeError as error:
        result["errors"].append(f"Invalid JSON: {error}")
        return
    if event.get("kind") != "commit":
        return
    commit = event.get("commit") or {}
    if commit.get("operation") != "create":
        return
    text = (commit.get("record") or {}).get("text", "")
    if not text:
        return
    count += 1
    if count <= 5:
        print(f"\nPost {count}: {text[:300]}")
    if count >= TARGET_EVENTS:
        result["status"] = "success"
        ws.close()


def on_error(ws, error):
    result["errors"].append(str(error))
    print("Error:", error)


def on_close(ws, code, reason):
    if result["status"] == "running":
        result["status"] = "partial_success" if count else "failed"
    result["close_code"] = code
    result["close_reason"] = reason
    save_result()
    print("Connection closed:", code, reason)
    print("Post events received:", count)


if __name__ == "__main__":
    ws = websocket.WebSocketApp(URL, on_open=on_open, on_message=on_message,
                                on_error=on_error, on_close=on_close)
    timer = threading.Timer(TIMEOUT_SECONDS, ws.close)
    timer.start()
    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    finally:
        timer.cancel()
        if "finished_at_utc" not in result:
            save_result()
