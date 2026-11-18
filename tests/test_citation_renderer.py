import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(importlib.util.find_spec("citracer"), "Requires the optional citracer environment")
class CitationRendererTests(unittest.TestCase):
    def test_offline_html_uses_utf8_with_windows_locale(self):
        data = {
            "nodes": [
                {"id": "A", "title": "Start", "roles": ["R1"], "year": 2025},
                {"id": "B", "title": "Bridge", "roles": ["R2"], "year": 2024},
                {"id": "C", "title": "Earlier", "roles": ["R3"], "year": 2023},
            ],
            "edges": [
                {
                    "source": "A", "target": "B",
                    "purpose_class": "background_or_introduction",
                    "applied_context_score": 0.5,
                    "context_sentence": "Earlier work is introduced.",
                },
                {"source": "B", "target": "C"},
            ],
        }
        renderer = Path(__file__).resolve().parents[1] / "scripts/render_citation_workspace.py"
        environment = dict(os.environ, PYTHONUTF8="0")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "input.json"
            output = Path(temporary) / "graph.html"
            source.write_text(json.dumps(data), encoding="utf-8")
            process = subprocess.run(
                [sys.executable, "-X", "utf8=0", str(renderer), str(source), str(output)],
                env=environment, capture_output=True, timeout=60,
            )
            self.assertEqual(process.returncode, 0, process.stderr.decode(errors="replace"))
            html = output.read_text(encoding="utf-8")
            self.assertIn("Earlier work is introduced.", html)
            self.assertIn("sugiyama-depth", html)
            self.assertIn("©", html)


if __name__ == "__main__":
    unittest.main()
