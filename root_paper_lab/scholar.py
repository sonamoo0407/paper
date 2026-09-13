"""Reuse the reviewed Scholar Search MCP client; add bounded paging and audit logs."""
import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import quote

from .core import now

FIELDS = ["paperId", "title", "year", "authors", "venue", "url", "externalIds", "referenceCount", "openAccessPdf"]


class Scholar:
    def __init__(self, run):
        vendor = Path(__file__).resolve().parents[1] / "vendor" / "scholar-search-mcp"
        sys.path.insert(0, str(vendor)) if str(vendor) not in sys.path else None
        from scholar_search_mcp.server import SemanticScholarClient
        self.api = SemanticScholarClient(os.environ.get("SEMANTIC_SCHOLAR_API_KEY"))
        self.run = run

    async def request(self, endpoint, params):
        # Timeout bounds the upstream exponential retry loop. Never serialize headers/errors.
        started = now()
        try:
            result = await asyncio.wait_for(self.api._request("GET", endpoint, params=params), timeout=55)
        except Exception as e:
            self.run.event("scholar_request_failed", {"endpoint": endpoint, "params": params,
                "started_utc": started, "error_type": type(e).__name__})
            raise
        self.run.event("scholar_response", {"endpoint": endpoint, "params": params,
            "started_utc": started, "retrieved_utc": now(), "response": result})
        return result

    async def search(self, query, limit=10, year=None):
        if not query.strip() or len(query) > 2000 or not 1 <= limit <= 50:
            raise ValueError("query required (max 2000 chars); limit 1..50")
        params = {"query": query, "limit": limit, "fields": ",".join(FIELDS)}
        if year:
            params["year"] = year
        return await self.request("paper/search", params)

    async def details(self, pid):
        return await self.request("paper/" + quote(pid, safe=""), {"fields": ",".join(FIELDS)})

    async def references(self, pid, limit):
        rows, offset, seen = [], 0, set()
        while len(rows) < limit:
            params = {"fields": ",".join(FIELDS + ["contexts", "intents"]),
                      "limit": min(100, limit-len(rows)), "offset": offset}
            page = await self.request("paper/" + quote(pid, safe="") + "/references", params)
            rows.extend(page.get("data") or [])
            nxt = page.get("next")
            if nxt is None:
                return {"data": rows, "truncated": False}
            if nxt in seen or nxt <= offset:
                raise ValueError("Non-progressing pagination")
            seen.add(nxt)
            offset = nxt
        return {"data": rows[:limit], "truncated": True}
