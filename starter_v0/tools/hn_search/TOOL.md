---
name: hn_search
track: core
kind: live_api
provider: Hacker News (Algolia API)
requires_env: []
inputs: [query, limit]
outputs: [items]
side_effect: false
---
# hn_search

Searches Hacker News stories by keyword via the public Algolia API (no key needed).
Returns title, url, points/comments summary and date for each story.