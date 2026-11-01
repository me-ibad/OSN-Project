# Authenticated Bluesky pagination test

This test uses the official `atproto` Python client and reads credentials only from
shell environment variables. It does not write a password, access token, or handle
to disk.

1. In Bluesky, create an **app password** for this project. Do not use your main
   Bluesky password.
2. In the terminal, set the credentials for the current shell only:

```bash
export BSKY_HANDLE='your-handle.bsky.social'
export BSKY_APP_PASSWORD='your-app-password'
```

3. Run the two-page test:

```bash
.venv/bin/python authenticated_paginated_search.py \
  --query 'AI software developers' --page-size 25 --max-pages 2
```

The output contains page counts and an overall status. It writes
`authenticated_search_result.json`, which never contains credentials or raw posts.

- `completed`: all requested pages completed and the last page had no next cursor.
- `partial_success`: at least one page returned posts but pagination did not finish.
- `failed`: no posts were returned.
