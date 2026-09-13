"""Pure graph logic and append-only research artifacts (standard library only)."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(paper):
    ids = paper.get("externalIds") or {}
    doi = (ids.get("DOI") or "").strip().lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    if doi:
        return "doi:" + doi
    if paper.get("paperId"):
        return "s2:" + paper["paperId"]
    if ids.get("ArXiv"):
        return "arxiv:" + re.sub(r"v\d+$", "", ids["ArXiv"])
    # Never silently merge title-only references: same-title papers exist.
    return "unresolved:" + uuid.uuid4().hex


class Run:
    def __init__(self, base, track, request):
        if track not in {"ai", "cybersecurity"}:
            raise ValueError("track must be ai or cybersecurity; do not mix tracks")
        self.path = Path(base).resolve() / track / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12])
        self.path.mkdir(parents=True, exist_ok=False)
        self.write("request.json", {"at_utc": now(), "track": track, "request": request})

    def write(self, name, value):
        target = (self.path / name).resolve()
        target.relative_to(self.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as f:
            f.write(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))
        return str(target)

    def event(self, operation, value):
        return self.write("events/" + uuid.uuid4().hex + ".json", {"at_utc": now(), "operation": operation, "data": value})


async def build_graph(client, seeds, depth=2, max_nodes=100, max_refs=100):
    if not 1 <= depth <= 3 or not 2 <= max_nodes <= 500 or not 1 <= max_refs <= 1000:
        raise ValueError("depth 1..3, max_nodes 2..500, max_refs 1..1000")
    if not seeds or len(seeds) > 20:
        raise ValueError("Provide 1..20 seed IDs")
    nodes, edges, seed_keys, failures, boundaries = {}, {}, [], [], []
    queue = deque()
    # Resolve all seed identities before traversal so duplicates cannot inflate coverage.
    for seed in seeds:
        try:
            p = await client.details(seed)
            key = canonical(p)
            if key not in nodes:
                if len(nodes) >= max_nodes:
                    boundaries.append({"reason": "node_limit", "seed": seed})
                    continue
                nodes[key] = p
                queue.append((key, 0))
            if key not in seed_keys:
                seed_keys.append(key)
        except Exception as e:
            failures.append({"seed": seed, "error_type": type(e).__name__})
    visited = set()
    while queue:
        key, level = queue.popleft()
        if key in visited or level >= depth:
            continue
        visited.add(key)
        pid = nodes[key].get("paperId")
        if not pid:
            boundaries.append({"node": key, "reason": "unresolved_identifier"})
            continue
        try:
            result = await client.references(pid, max_refs)
        except Exception as e:
            failures.append({"node": key, "error_type": type(e).__name__})
            continue
        if result.get("truncated"):
            boundaries.append({"node": key, "reason": "reference_limit"})
        for row in result["data"]:
            p = row.get("citedPaper")
            if not p or not p.get("title"):
                boundaries.append({"node": key, "reason": "unresolved_reference"})
                continue
            dest = canonical(p)
            if dest == key:
                continue
            if dest not in nodes:
                if len(nodes) >= max_nodes:
                    boundaries.append({"node": key, "reason": "node_limit"})
                    continue
                nodes[dest] = p
                queue.append((dest, level + 1))
            edges[(key, dest)] = {"from": key, "to": dest,
                "contexts": row.get("contexts") or [], "intents": row.get("intents") or [],
                "evidence_status": "database_metadata_not_fulltext_verified"}
    adjacency = {}
    for a, b in edges:
        adjacency.setdefault(a, set()).add(b)
    candidates = []
    for key, paper in nodes.items():
        if key in seed_keys:
            continue
        paths, direct = {}, []
        for seed in seed_keys:
            if key in adjacency.get(seed, set()):
                direct.append(seed)
            q = deque([(seed, [seed])])
            seen = {seed}
            while q:
                at, path = q.popleft()
                if len(path) - 1 >= depth:
                    continue
                for nxt in sorted(adjacency.get(at, set())):
                    if nxt == key:
                        paths[seed] = path + [nxt]
                        q.clear()
                        break
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append((nxt, path + [nxt]))
        candidates.append({"id": key, "title": paper["title"], "seed_coverage": len(paths),
            "resolved_seed_count": len(seed_keys), "direct_seed_count": len(direct),
            "paths": paths, "root_status": "candidate_only", "foundational_reason": "확인 불가: 인용 문맥과 원문 검토 필요"})
    candidates.sort(key=lambda r: (-r["seed_coverage"], -r["direct_seed_count"], r["title"]))
    return {"nodes": nodes, "edges": list(edges.values()), "seed_ids": seed_keys,
        "candidates": candidates, "failures": failures, "boundaries": boundaries,
        "coverage_note": "설정 깊이·한도 내 DB 관측 결과. 전체 참고문헌의 완전성 또는 절대적 시발점을 보장하지 않음."}


def graph_report(graph):
    lines = ["# 루트논문 후보", "", graph["coverage_note"], "",
             "순서는 출발 논문별 도달 수, 직접 인용 수 기준이며 품질 점수가 아니다.", ""]
    for i, r in enumerate(graph["candidates"], 1):
        lines += [f"## {i}. {r['title']}", "", f"- 식별자: {r['id']}",
                  f"- 출발 논문 도달 수: {r['seed_coverage']}/{r['resolved_seed_count']}",
                  f"- 직접 인용 출발 논문 수: {r['direct_seed_count']}",
                  "- 루트 판정: 후보. 원문 미분석, 실험 미재현.", "- 이유: " + r["foundational_reason"], ""]
    lines += [f"조회 실패: {len(graph['failures'])}건 / 탐색 경계: {len(graph['boundaries'])}건"]
    return "\n".join(lines)


def archive_pdf(run, source, paper_id, provenance):
    source = Path(source).resolve()
    if source.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("PDF exceeds 50 MiB limit")
    data = source.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError("Not a PDF")
    return archive_pdf_bytes(run, data, paper_id, provenance, str(source))


def archive_pdf_bytes(run, data, paper_id, provenance, source):
    if len(data) > 50 * 1024 * 1024 or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF or size limit exceeded")
    digest = hashlib.sha256(data).hexdigest()
    target = run.path / (digest + ".pdf")
    with target.open("xb") as f:
        f.write(data)
    manifest = {"paper_id": paper_id, "sha256": digest, "file": str(target),
                "source": str(source), "provenance": provenance, "at_utc": now(),
                "identity_status": "operator_supplied_not_verified", "fulltext_read": False, "experiment_reproduced": False}
    run.write("pdf-manifest.json", manifest)
    return manifest
