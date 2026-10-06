"""Small live check: official ACL index only; no PDF or model call."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from root_paper_lab.server import collect_top_venue_papers


async def main():
    result = await collect_top_venue_papers(
        track="ai",
        query="agent security",
        venues_csv="acl",
        year_start=2025,
        year_end=2025,
        max_results=3,
        top_tier_only=True,
    )
    print(json.dumps({
        "status": result["status"],
        "count": result["count"],
        "source_status": result["sources"],
        "titles": [paper["title"] for paper in result["papers"]],
        "run": result["run"],
        "pdf_downloaded": result["pdf_downloaded"],
        "paperqa_run": result["paperqa_run"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
