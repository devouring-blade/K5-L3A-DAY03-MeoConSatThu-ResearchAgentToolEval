from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

HN_API = "https://hn.algolia.com/api/v1/search"
HN_ITEM = "https://news.ycombinator.com/item?id="


def search_hacker_news(query: str = "", limit: int = 5) -> dict[str, Any]:
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 5
        limit = max(1, min(limit, 20))
        response = requests.get(
            HN_API,
            params={"query": query, "tags": "story", "hitsPerPage": limit},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", [])[:limit]:
            story_id = hit.get("objectID")
            items.append({
                "title": hit.get("title"),
                "url": hit.get("url") or (f"{HN_ITEM}{story_id}" if story_id else ""),
                "source": "news.ycombinator.com",
                "summary": f"{hit.get('points') or 0} points, {hit.get('num_comments') or 0} comments",
                "date": hit.get("created_at"),
            })
        return {"tool": "hn_search", "query": query, "items": items}
    except Exception as exc:
        return err("hn_search", exc)