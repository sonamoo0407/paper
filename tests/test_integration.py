import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

from root_paper_lab.core import Run
from root_paper_lab.scholar import Scholar
from root_paper_lab import server


class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_paging(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = Scholar(Run(tmp, "ai", {}))
            c.request = AsyncMock(side_effect=[{"data": [{"citedPaper": {"title": "a"}}], "next": 1},
                                             {"data": [{"citedPaper": {"title": "b"}}]}])
            result = await c.references("abc", 10)
            self.assertEqual(len(result["data"]), 2)
            self.assertFalse(result["truncated"])
            self.assertEqual(c.request.call_args_list[1].args[1]["offset"], 1)

    async def test_paging_stall(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = Scholar(Run(tmp, "ai", {}))
            c.request = AsyncMock(return_value={"data": [], "next": 0})
            with self.assertRaises(ValueError):
                await c.references("abc", 10)

    async def test_model_authorization_gate(self):
        result = await server.analyze_root_paper("ai", "nonexistent", "test", "model", "embed")
        self.assertEqual(result["status"], "needs_authorization")

    async def test_download_blocks_private_host(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "BASE", Path(tmp)):
            result = await server.download_root_pdf("ai", "test", "https://127.0.0.1/secret")
            self.assertEqual(result["status"], "failed")

    async def test_tool_surface_no_destructive_upstream_tool(self):
        tools = await server.mcp.list_tools()
        names = {t.name for t in tools}
        self.assertIn("trace_root_papers", names)
        self.assertIn("analyze_root_paper", names)
        self.assertNotIn("download_arxiv_source", names)

    async def test_paperqa_adapter_mocked_model(self):
        from paperqa import Docs
        from root_paper_lab.core import archive_pdf_bytes
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "BASE", Path(tmp)):
            run = Run(tmp, "ai", {})
            archive_pdf_bytes(run, b"%PDF-1.7\nmock", "R", "fixture", "fixture")
            answer = SimpleNamespace(formatted_answer="Mock answer with source", contexts=[
                SimpleNamespace(context="Mock evidence", score=8,
                                text=SimpleNamespace(name="R pages 1-2", text="Mock original"))])
            with patch.object(Docs, "aadd", new=AsyncMock()) as add, patch.object(Docs, "aquery", new=AsyncMock(return_value=answer)):
                result = await server.analyze_root_paper("ai", str(run.path / "pdf-manifest.json"),
                    "test", "test-model", "test-embedding", True)
                self.assertEqual(result["status"], "draft_generated")
                self.assertEqual(result["evidence_count"], 1)
                self.assertTrue((Path(result["run"]) / "evidence.json").exists())
                add.assert_awaited_once()
            with self.assertRaises(ValueError):
                await server.analyze_root_paper("cybersecurity", str(run.path / "pdf-manifest.json"),
                    "test", "test-model", "test-embedding", True)


if __name__ == "__main__":
    unittest.main()
