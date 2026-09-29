"""Explicit, bounded public API smoke test. No PDF or model calls."""
import asyncio
import json
from root_paper_lab.core import Run
from root_paper_lab.scholar import Scholar


async def main():
    run = Run("runs", "ai", {"purpose": "live API smoke test, not research selection", "seed": "ARXIV:2409.13740"})
    client = Scholar(run)
    try:
        p = await client.details("ARXIV:2409.13740")
        refs = await client.references(p["paperId"], 3)
        result = {"status": "passed", "title": p["title"], "reference_rows": len(refs["data"]),
                  "truncated": refs["truncated"], "run": str(run.path)}
    except Exception as e:
        result = {"status": "failed", "error_type": type(e).__name__, "run": str(run.path)}
    run.write("live-check.json", result)
    print(json.dumps(result, ensure_ascii=True))


asyncio.run(main())
