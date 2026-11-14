#!/usr/bin/env python3
"""Build an allowlist-only public bundle for a bounded dry-run."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FILES = (
    'ledger/r1_candidates.json',
    'ledger/r2_citation_ledger.json',
    'logs/search_log.json',
    'graph/graph.json',
    'verification/dryrun_verification.json',
    'graph/graph_ui_analysis_note_compact_test_20260930T001100Z/analysis_note_verification.json',
    'graph/graph_ui_analysis_note_compact_test_20260930T001100Z/verify_analysis_note.py',
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.exists() and {p.name for p in output.iterdir()} - {'README.md'}:
        raise SystemExit(f'Refusing to overwrite nonempty bundle: {output}')
    output.mkdir(parents=True, exist_ok=True)
    for rel in FILES:
        src = source / rel
        if not src.is_file():
            raise SystemExit(f'Missing allowlisted source: {src}')
        dst = output / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    html = (source / 'graph/graph_ui_analysis_note_compact_test_20260930T001100Z/index.html').read_text(encoding='utf-8')
    html = html.replace(str(source), '${RESEARCH_DATA}/ransomware_detection_dryrun_20260929T231104Z')
    (output / 'graph/index.html').parent.mkdir(parents=True, exist_ok=True)
    (output / 'graph/index.html').write_text(html, encoding='utf-8')


if __name__ == '__main__':
    main()
