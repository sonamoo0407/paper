"""Bounded, OA-only smoke test; upstream code remains unchanged."""
import argparse
import json
import logging
import threading
from pathlib import Path
from unittest.mock import patch

import fitz
from citracer import analytics, pdf_parser, tracer, visualizer
from citracer.exporter import export_graph
from citracer.reference_resolver import ReferenceResolver, ResolvedRef
from citracer.utils import make_paper_id, normalize_title


class BoundedOAResolver(ReferenceResolver):
    def __init__(self, cache_dir, limit, local_pdfs=None):
        super().__init__(cache_dir=cache_dir)
        self.limit = limit
        self.attempted = 0
        self.guard = threading.Lock()
        self.local_pdfs = local_pdfs or {}

    def prefetch(self, bibs):
        # Avoid querying every bibliography item before the bounded test.
        pass

    def batch_enrich(self, refs):
        if self.limit == 0:
            return None
        return super().batch_enrich(refs)

    def _download_scihub(self, doi):
        return None

    def s2_by_id(self, paper_id):
        # tracer also enriches the root outside resolve(); disable that
        # implicit network lookup in the local-only mode.
        if self.limit == 0:
            return None
        return super().s2_by_id(paper_id)

    def resolve(self, bib):
        local_pdf = self.local_pdfs.get(normalize_title(bib.title or ''))
        if local_pdf:
            return ResolvedRef(
                paper_id=make_paper_id(doi=bib.doi, arxiv_id=bib.arxiv_id,
                                      title=bib.title),
                title=bib.title, authors=bib.authors, year=bib.year,
                doi=bib.doi, arxiv_id=bib.arxiv_id, pdf_path=local_pdf,
            )
        with self.guard:
            allowed = self.attempted < self.limit
            if allowed:
                self.attempted += 1
        if allowed:
            return super().resolve(bib)
        return ResolvedRef(
            paper_id=make_paper_id(doi=bib.doi, arxiv_id=bib.arxiv_id,
                                  title=bib.title or bib.raw),
            title=bib.title or bib.raw, authors=bib.authors,
            year=bib.year, doi=bib.doi, arxiv_id=bib.arxiv_id,
        )


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pdf', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--keyword', default='phishing')
    p.add_argument('--resolve-limit', type=int, default=2)
    p.add_argument('--inspect-only', action='store_true')
    p.add_argument('--local-corpus', help='JSON list of {title, path} for already obtained PDFs')
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pdf = Path(args.pdf).resolve()
    assert pdf.read_bytes().startswith(b'%PDF-'), 'Not a PDF'
    with fitz.open(pdf) as doc:
        pages = len(doc)
    original_parse = pdf_parser.parse

    def local_parse(*a, **kw):
        # No Crossref header consolidation: document parsing stays local.
        kw['consolidate_header'] = False
        kw['consolidate_citations'] = False
        return original_parse(*a, **kw)

    parsed = local_parse(pdf, grobid_url='http://127.0.0.1:18070',
                         cache_dir=out / 'cache')
    inspection = dict(title=parsed.title, pages=pages,
                      references=len(parsed.bibliography),
                      inline_citations=len(parsed.inline_refs),
                      bibliography=[vars(b) for b in parsed.bibliography.values()])
    (out / 'inspection.json').write_text(json.dumps(inspection, indent=2,
                                                    ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in inspection.items() if k != 'bibliography'},
                     ensure_ascii=True), flush=True)
    if args.inspect_only:
        return
    local_pdfs = {}
    if args.local_corpus:
        entries = json.loads(Path(args.local_corpus).read_text(encoding='utf-8'))
        local_pdfs = {normalize_title(e['title']): Path(e['path']).resolve() for e in entries}
    resolver = BoundedOAResolver(out / 'cache', args.resolve_limit, local_pdfs)
    try:
        with patch.object(pdf_parser, 'parse', local_parse):
            graph = tracer.trace(pdf, args.keyword, max_depth=1,
                                 cache_dir=out / 'cache',
                                 grobid_url='http://127.0.0.1:18070',
                                 grobid_workers=1, resolver=resolver)
    finally:
        resolver.close()
    metrics = analytics.analyze(graph)
    for ext in ('json', 'graphml', 'csv'):
        export_graph(graph, out / f'graph.{ext}', analytics=metrics)
    visualizer.render(graph, out / 'graph.html', keyword=args.keyword,
                      show_details=True, analytics=metrics)
    report = dict(nodes=len(graph.nodes), edges=len(graph.edges),
                  pdfs_analyzed=sum(n.status in ('root', 'analyzed', 'no_match')
                                    for n in graph.nodes.values()),
                  keyword_passages=sum(len(n.keyword_hits) for n in graph.nodes.values()),
                  edges_with_context=sum(bool(e.context) for e in graph.edges),
                  external_resolve_attempts=resolver.attempted,
                  policy='Sci-Hub disabled; OA only; depth 1; capped lookups',
                  limitation='Unresolved includes test-cap-skipped references; not an exhaustive availability check.',
                  node_statuses={pid: n.status for pid, n in graph.nodes.items()})
    assert graph.nodes and report['keyword_passages'] > 0
    assert all(e.source_id in graph.nodes and e.target_id in graph.nodes for e in graph.edges)
    (out / 'report.json').write_text(json.dumps(report, indent=2,
                                               ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
