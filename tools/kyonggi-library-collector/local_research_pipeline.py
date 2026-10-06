"""Token-free local preprocessing for the Kyonggi paper workflow.

This program deliberately uses deterministic scoring, PDF text extraction, DOI
matching, and browser-independent HTML rendering.  It never calls an LLM or
sends paper text to a remote model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

from kyonggi_collector import prioritize_records


DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", re.I)
WORD_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.I)


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def words(value: str) -> list[str]:
    stop = {
        "and", "the", "for", "with", "from", "that", "this", "using", "based", "into", "via",
        "of", "in", "on", "to", "a", "an", "is", "are", "by", "as", "at", "be", "or",
    }
    return [word.lower() for word in WORD_RE.findall(value) if word.lower() not in stop]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def normal_title(value: str) -> str:
    return " ".join(words(value))


def deduplicate(records: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
    seen: set[str] = set()
    output: list[dict[str, object]] = []
    for record in records:
        doi = str(record.get("doi") or "").lower().rstrip(".,;)")
        key = f"doi:{doi}" if doi else f"title:{normal_title(str(record.get('title') or ''))}"
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(dict(record))
    return output, len(records) - len(output)


def bm25_scores(records: list[dict[str, object]], query: str) -> list[float]:
    """Small local BM25 implementation; scores title/source/visible metadata."""
    query_terms = words(query)
    documents = [
        words(
            " ".join(
                str(record.get(field) or "")
                for field in ("title", "publication_source", "display_metadata", "authors")
            )
        )
        for record in records
    ]
    if not query_terms or not documents:
        return [0.0] * len(records)
    doc_freq = Counter(term for document in documents for term in set(document))
    avg_len = sum(map(len, documents)) / len(documents) or 1
    scores: list[float] = []
    for document in documents:
        freq = Counter(document)
        score = 0.0
        for term in query_terms:
            if term not in freq:
                continue
            idf = math.log(1 + (len(documents) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            score += idf * (freq[term] * 2.2) / (freq[term] + 1.2 * (1 - 0.75 + 0.75 * len(document) / avg_len))
        scores.append(score)
    return scores


def prepare(args: argparse.Namespace) -> int:
    source = Path(args.records)
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    raw = read_jsonl(source)
    unique, duplicates = deduplicate(raw)
    ranked = prioritize_records(unique, args.priority)
    relevance = bm25_scores(ranked, args.query)
    max_relevance = max(relevance, default=0.0) or 1.0
    for item, score in zip(ranked, relevance):
        item["local_relevance_score"] = round(score / max_relevance * 100, 2)
        # Venue quality has greater influence than keyword repetition, but both
        # remain visible and reproducible in the saved selection file.
        item["local_selection_score"] = round(float(item["priority_score"]) + item["local_relevance_score"] * 0.35, 2)
    ranked.sort(key=lambda item: (-float(item["local_selection_score"]), int(item["priority_rank"])))
    for rank, item in enumerate(ranked, start=1):
        item["local_selection_rank"] = rank
        item["local_selection_reason"] = (
            f"venue={item['priority_tier']} ({item['priority_score']}), "
            f"local BM25 relevance={item['local_relevance_score']}"
        )
    selected = ranked[: args.select_count]
    write_jsonl(target / "candidates_ranked.jsonl", ranked)
    write_jsonl(target / "selected_candidates.jsonl", selected)
    fields = [
        "local_selection_rank", "local_selection_score", "priority_tier", "priority_score",
        "local_relevance_score", "candidate_id", "title", "authors", "year", "publication_source",
        "doi", "fulltext_url", "local_selection_reason",
    ]
    with (target / "selected_candidates.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(selected)
    (target / "prepare_manifest.json").write_text(
        json.dumps(
            {
                "mode": "local-token-free-prepare",
                "query": args.query,
                "priority": args.priority,
                "input_records": len(raw),
                "duplicates_removed": duplicates,
                "ranked_records": len(ranked),
                "selected_records": len(selected),
                "method": "metadata normalization, DOI/title deduplication, venue heuristic, and local BM25; no LLM or remote model calls",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Prepared {len(ranked)} records; selected top {len(selected)} -> {target.resolve()}")
    return 0


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return cleaned or "paper"


def section_excerpt(text: str, heading: str, limit: int = 1600) -> str:
    match = re.search(rf"(?im)^\s*{heading}\s*$", text)
    if not match:
        return ""
    tail = text[match.end() :]
    next_heading = re.search(r"(?im)^\s*(?:\d+\.?\s+)?(?:introduction|method(?:ology)?|results?|discussion|conclusion|references)\s*$", tail)
    return " ".join((tail[: next_heading.start()] if next_heading else tail[:limit]).split())[:limit]


def pdf_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_pdfs(args: argparse.Namespace) -> int:
    try:
        import pymupdf
    except ImportError as exc:
        raise SystemExit("PyMuPDF is required. Run: pip install -r requirements.txt") from exc
    selected = read_jsonl(Path(args.selected_records))
    pdf_root = Path(args.pdf_dir)
    target = Path(args.output_dir)
    text_dir = target / "extracted_text"
    text_dir.mkdir(parents=True, exist_ok=True)
    pdfs = list(pdf_root.rglob("*.pdf"))
    rows: list[dict[str, object]] = []
    for pdf in pdfs:
        candidate = next((item for item in selected if str(item.get("candidate_id") or "").lower() in pdf.name.lower()), None)
        try:
            document = pymupdf.open(pdf)
            text = "\n".join(page.get_text("text") for page in document)
            page_count = document.page_count
            document.close()
            candidate_id = str(candidate.get("candidate_id")) if candidate else safe_id(pdf.stem)
            text_path = text_dir / f"{safe_id(candidate_id)}.txt"
            text_path.write_text(text, encoding="utf-8")
            refs = section_excerpt(text, "references", limit=max(len(text), 1))
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "pdf_file": str(pdf.resolve()),
                    "text_file": str(text_path.resolve()),
                    "sha256": pdf_sha256(pdf),
                    "page_count": page_count,
                    "text_characters": len(text),
                    "doi_references": sorted(set(match.rstrip(".,;)") for match in DOI_RE.findall(refs))),
                    "abstract_excerpt": section_excerpt(text, "abstract"),
                    "method_excerpt": section_excerpt(text, "method(?:ology)?"),
                    "status": "extracted" if len(text.strip()) >= 200 else "low_text_or_scanned_pdf",
                }
            )
        except Exception as exc:
            rows.append({"pdf_file": str(pdf.resolve()), "status": f"failed_{type(exc).__name__}"})
    write_jsonl(target / "pdf_extraction.jsonl", rows)
    (target / "pdf_extraction_manifest.json").write_text(
        json.dumps(
            {"mode": "local-pdf-extraction", "pdfs_seen": len(pdfs), "rows": len(rows), "llm_calls": 0},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Extracted {sum(row.get('status') == 'extracted' for row in rows)}/{len(pdfs)} PDFs -> {target.resolve()}")
    return 0


def build_graph(args: argparse.Namespace) -> int:
    selected = read_jsonl(Path(args.selected_records))
    extracted = {str(row.get("candidate_id")): row for row in read_jsonl(Path(args.extraction))}
    doi_to_id = {
        str(record.get("doi") or "").lower().rstrip(".,;)"): str(record.get("candidate_id"))
        for record in selected
        if record.get("doi")
    }
    nodes = [
        {
            "id": str(record.get("candidate_id")),
            "title": record.get("title"),
            "year": record.get("year"),
            "tier": record.get("priority_tier"),
            "score": record.get("local_selection_score", record.get("priority_score", 0)),
        }
        for record in selected
    ]
    edges: list[dict[str, object]] = []
    for source_id, row in extracted.items():
        for doi in row.get("doi_references", []):
            target_id = doi_to_id.get(str(doi).lower())
            if target_id and target_id != source_id:
                edges.append({"source": source_id, "target": target_id, "evidence": "reference DOI exact match"})
    # A local title match is only supplemental evidence and is deliberately strict.
    for left in selected:
        source_id = str(left.get("candidate_id"))
        row = extracted.get(source_id, {})
        text_path = Path(str(row.get("text_file") or ""))
        if not text_path.is_file():
            continue
        references = section_excerpt(text_path.read_text(encoding="utf-8", errors="replace"), "references", limit=120000)
        for right in selected:
            target_id = str(right.get("candidate_id"))
            if target_id == source_id or any(edge["source"] == source_id and edge["target"] == target_id for edge in edges):
                continue
            title = normal_title(str(right.get("title") or ""))
            if len(title) < 20:
                continue
            ratio = SequenceMatcher(None, title, normal_title(references)).ratio()
            # The complete-reference-string ratio is weak, so only include an
            # exact normalized-title substring as a deterministic title match.
            if title in normal_title(references):
                edges.append({"source": source_id, "target": target_id, "evidence": "reference title exact normalized match", "similarity": round(ratio, 3)})
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    graph = {"generated_utc": utc_now(), "method": "local DOI/title reference matching; no LLM", "nodes": nodes, "edges": edges}
    (target / "citation_graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    html = """<!doctype html><meta charset='utf-8'><title>Local Citation Graph</title>
<style>body{margin:0;background:#122033;color:#eaf2ff;font:14px system-ui}#g{width:100vw;height:100vh}line{stroke:#7cd4c3;stroke-width:2}circle{fill:#6db4e5;stroke:#fff;stroke-width:2}text{fill:#fff;font-size:12px}</style>
<svg id='g'></svg><script>fetch('citation_graph.json').then(r=>r.json()).then(x=>{const s=document.querySelector('#g'),w=innerWidth,h=innerHeight,n=x.nodes;const p={};n.forEach((a,i)=>p[a.id]=[100+(i%5)*(w-180)/4,100+Math.floor(i/5)*120]);x.edges.forEach(e=>{let l=document.createElementNS('http://www.w3.org/2000/svg','line');[l.x1,l.y1]=p[e.source]||[0,0];[l.x2,l.y2]=p[e.target]||[0,0];s.append(l)});n.forEach(a=>{let [x,y]=p[a.id],c=document.createElementNS('http://www.w3.org/2000/svg','circle'),t=document.createElementNS('http://www.w3.org/2000/svg','text');c.setAttribute('cx',x);c.setAttribute('cy',y);c.setAttribute('r',25);t.setAttribute('x',x-22);t.setAttribute('y',y+5);t.textContent=a.id;s.append(c,t)})})</script>"""
    (target / "citation_graph.html").write_text(html, encoding="utf-8")
    print(f"Built local graph: {len(nodes)} nodes, {len(edges)} evidence-backed edges -> {target.resolve()}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Token-free local research preprocessing")
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("prepare", help="Deduplicate and rank metadata locally before any PDF analysis")
    a.add_argument("--records", required=True)
    a.add_argument("--query", required=True)
    a.add_argument("--output-dir", required=True)
    a.add_argument("--select-count", type=int, default=30)
    a.add_argument("--priority", choices=("top-tier", "source-order"), default="top-tier")
    b = sub.add_parser("extract", help="Extract PDF text, reference DOIs, and deterministic evidence locally")
    b.add_argument("--selected-records", required=True)
    b.add_argument("--pdf-dir", required=True)
    b.add_argument("--output-dir", required=True)
    c = sub.add_parser("graph", help="Build a citation graph from extracted local PDF evidence")
    c.add_argument("--selected-records", required=True)
    c.add_argument("--extraction", required=True)
    c.add_argument("--output-dir", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "prepare":
        if args.select_count < 1:
            raise SystemExit("--select-count must be positive")
        return prepare(args)
    if args.command == "extract":
        return extract_pdfs(args)
    return build_graph(args)


if __name__ == "__main__":
    raise SystemExit(main())
