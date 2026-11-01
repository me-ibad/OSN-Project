
import requests

url = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"

params = {
    "q": "AI software developers",
    "limit": 100,
    "sort": "latest"
}

response = requests.get(url, params=params, timeout=30)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Response:", response.text[:500])

response.raise_for_status()

posts = response.json().get("posts", [])

print("Total posts:", len(posts))

for post in posts[:5]:
    print("---")
    print(post.get("record", {}).get("text", ""))

