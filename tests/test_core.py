import tempfile
import unittest
from pathlib import Path
from root_paper_lab.core import Run, archive_pdf, build_graph, canonical


def paper(pid, doi=None):
    return {"paperId": pid, "title": "Paper " + pid, "externalIds": {"DOI": doi} if doi else {}}


class FakeScholar:
    async def details(self, pid):
        if pid == "missing":
            raise LookupError()
        return paper(pid)

    async def references(self, pid, limit):
        refs = {"A": ["R", "X", "R"], "B": ["X"], "X": ["R"], "R": ["A"]}
        return {"data": [{"citedPaper": paper(x)} for x in refs.get(pid, [])[:limit]],
                "truncated": len(refs.get(pid, [])) > limit}


class GraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_shared_roots_paths_cycles_and_duplicate_seeds(self):
        g = await build_graph(FakeScholar(), ["A", "A", "B"])
        r = next(r for r in g["candidates"] if r["id"] == "s2:R")
        self.assertEqual(r["seed_coverage"], 2)
        self.assertEqual(r["direct_seed_count"], 1)
        self.assertEqual(r["resolved_seed_count"], 2)
        self.assertEqual(r["paths"]["s2:B"], ["s2:B", "s2:X", "s2:R"])
        self.assertEqual(len(g["edges"]), 5)

    async def test_failure_is_not_no_references(self):
        g = await build_graph(FakeScholar(), ["missing"])
        self.assertEqual(len(g["failures"]), 1)
        self.assertEqual(g["candidates"], [])

    async def test_bounds(self):
        g = await build_graph(FakeScholar(), ["A", "B"], max_nodes=3, max_refs=1)
        self.assertLessEqual(len(g["nodes"]), 3)
        self.assertTrue(g["boundaries"])
        with self.assertRaises(ValueError):
            await build_graph(FakeScholar(), ["A"], depth=9)

    async def test_doi_normalization(self):
        self.assertEqual(canonical(paper("a", "https://doi.org/10.1/ABC")), canonical(paper("b", "10.1/abc")))
        self.assertNotEqual(canonical({"title": "Same"}), canonical({"title": "Same"}))


class ArchiveTests(unittest.TestCase):
    def test_immutable_and_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = Run(tmp, "ai", {"query": "test"})
            r.write("test.txt", "old")
            with self.assertRaises(FileExistsError):
                r.write("test.txt", "new")
            with self.assertRaises(ValueError):
                r.write("../../../../escape", "bad")
            p = Path(tmp) / "input.pdf"
            p.write_bytes(b"%PDF-1.7\nfixture only")
            m = archive_pdf(r, p, "test", "fixture")
            self.assertEqual(len(m["sha256"]), 64)
            self.assertTrue(p.exists())
            self.assertFalse(m["fulltext_read"])

    def test_track(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                Run(tmp, "mixed", {})


if __name__ == "__main__":
    unittest.main()
