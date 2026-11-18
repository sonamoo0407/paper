"""Build an offline citation explorer from a verified graph ledger."""

import argparse
import json
import re
from html import escape
from pathlib import Path
from unittest.mock import patch

from citracer import analytics, visualizer
from citracer.models import CitationEdge, PaperNode, TracerGraph
from citracer.utils import normalize_doi


def read_graph(path):
    source = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".html":
        match = re.search(r"\bconst D\s*=\s*", source)
        if not match:
            raise ValueError("Use the graph JSON or the earlier embedded evidence HTML")
        return json.JSONDecoder().raw_decode(source[match.end():])[0]
    return json.loads(source)


def publication_year(row):
    for field in ("year", "publication_year", "publication_date", "issued"):
        value = row.get(field)
        if isinstance(value, dict):
            parts = value.get("date-parts") or [[]]
            value = next(iter(parts[0]), None)
        match = re.match(r"^((?:18|19|20)\d{2})(?:\b|$)", str(value or ""))
        if match:
            return int(match[1])
    return None


def make_payload(data):
    papers = {}
    aliases = {}
    stage_names = ("R1", "R2", "R3")
    source_nodes = data["nodes"]
    if isinstance(source_nodes, dict):
        source_nodes = list(source_nodes.values())
    for row in source_nodes:
        original = row.get("id") or row["paper_id"]
        doi = normalize_doi(row.get("doi") or (original if original.lower().startswith(("doi:", "https://doi.org/", "10.")) else ""))
        if doi:
            doi = doi.removeprefix("doi:")
        key = f"doi:{doi}" if doi else original
        aliases[original] = key
        roles = row.get("roles") or row.get("layers") or [row.get("layer") or row.get("primary_layer")]
        if isinstance(roles, str):
            roles = [roles]
        roles = [role for role in roles if role in stage_names]
        if not roles and isinstance(row.get("depth"), int) and 0 <= row["depth"] < 3:
            roles = [stage_names[row["depth"]]]
        paper = papers.setdefault(key, {"id": key, "title": "", "roles": [], "reason": "", "years": set()})
        year = publication_year(row)
        if year:
            paper["years"].add(year)
        title = row.get("title")
        if title and title not in (key, original) and not paper["title"]:
            paper["title"] = title
        paper["roles"] = sorted(set(paper["roles"] + roles))
        paper["reason"] = paper["reason"] or row.get("selection_reason") or ""

    pairs = {}
    for row in data["edges"]:
        source = row.get("citing_id") or row.get("source_id") or row.get("source") or row.get("from")
        target = row.get("cited_id") or row.get("target_id") or row.get("target") or row.get("to")
        if source not in aliases or target not in aliases:
            raise ValueError(f"Missing endpoint: {source} → {target}")
        pair = aliases[source], aliases[target]
        if pair[0] == pair[1]:
            continue
        entry = pairs.setdefault(pair, {"source": pair[0], "target": pair[1], "records": []})
        entry["records"].append(row)
        if row.get("citing_pdf") and not papers[pair[0]]["title"]:
            papers[pair[0]]["title"] = Path(row["citing_pdf"].replace("\\", "/")).stem.replace("_", " ")

    graph = TracerGraph()
    for paper in papers.values():
        paper["title"] = paper["title"] or paper["id"]
        depth = stage_names.index(paper["roles"][0]) if paper["roles"] else 2
        status = ("root", "analyzed", "no_match")[depth]
        years = paper["years"]
        year = next(iter(years)) if len(years) == 1 else None
        graph.add_node(PaperNode(paper["id"], paper["title"], year=year, depth=depth, status=status))
    for source, target in pairs:
        graph.add_edge(CitationEdge(source, target))
    return graph, papers, pairs


PURPOSES = {
    "background_or_introduction": "배경·단순 소개",
    "adoption_or_extension": "채택·발전",
    "comparison_or_validation": "비교·검증",
    "limitation_or_critique": "한계 지적",
    "context_held": "판정 보류",
}


def edge_evidence(records):
    sections = []
    for row in records:
        context = row.get("context")
        context = context if isinstance(context, dict) else row
        evidence = context.get("evidence") or context
        if not isinstance(evidence, dict):
            evidence = context
        score = context.get("applied_context_score")
        purpose = PURPOSES.get(context.get("purpose_class"), "목적 미기록")
        location = [
            f"참고문헌 [{row['reference_number']}]" if row.get("reference_number") else "",
            f"참고문헌 PDF p.{row['reference_page']}" if row.get("reference_page") else "",
            f"본문 PDF p.{evidence['context_pdf_page']}" if evidence.get("context_pdf_page") else "",
        ]
        title = purpose if score is None else f"{purpose} · 문맥 점수 {float(score):+g}"
        sentence = evidence.get("context_sentence") or "연결된 본문 인용 문장이 없어."
        extra = [
            value for value in (
                evidence.get("preceding_sentence"), evidence.get("following_sentence"),
                context.get("rationale"), row.get("reference_text"),
            ) if value
        ]
        sections.append(
            f'<div class="hits"><strong>{escape(title)}</strong>'
            f'<p>{escape(" · ".join(filter(None, location)))}</p>'
            f'<blockquote>{escape(sentence)}</blockquote>'
            '<details><summary>주변 문맥과 판정 근거</summary>'
            + "".join(f"<p>{escape(str(value))}</p>" for value in extra)
            + "</details></div>"
        )
    return "".join(sections)


def customized_overlay(papers, pairs, title, central_paper, max_centrality):
    template = visualizer._load_overlay_template()
    node_evidence = {}
    edge_panels = {}
    for (source, target), pair in pairs.items():
        heading = f"{papers[source]['title']} → {papers[target]['title']}"
        evidence = edge_evidence(pair["records"])
        edge_panels.setdefault(source, {})[target] = f"<h3>{escape(heading)}</h3>{evidence}"
        link = f"<details><summary>{escape(heading)}</summary>{evidence}</details>"
        node_evidence.setdefault(source, []).append(link)
        node_evidence.setdefault(target, []).append(link)

    for node_id, paper in papers.items():
        intro = f"<p>인용 단계 {escape(' · '.join(paper['roles']) or '미기록')}</p>"
        if paper["reason"]:
            intro += f"<p>선정 이유 {escape(paper['reason'])}</p>"
        linked = "".join(node_evidence.get(node_id, []))
        node_evidence[node_id] = f"{intro}<h3>인용 근거</h3>{linked or '<p>연결 근거 없음</p>'}"

    def js(value):
        return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")

    legend = f"<strong>{escape(title)}</strong>"
    rules = {
        '<div>keyword: {{KEYWORD_CHIPS}}</div>': legend,
        'value="in-degree" selected': 'value="in-degree"',
        'value="betweenness">betweenness': 'value="betweenness" selected>매개중심성',
        'let currentSizeMode = "in-degree";': 'let currentSizeMode = "betweenness";',
        "base = 16 + 120 * Math.sqrt(nm.betweenness || 0);":
            f"base = 12 + 16 * Math.sqrt((nm.betweenness || 0) / {max_centrality or 1});",
        'if (d.status === "root") base = Math.max(base, 30);':
            'if (d.status === "root" && currentSizeMode !== "betweenness") base = Math.max(base, 30);',
        "nodeSpacing = 100; treeSpacing = 160; levelSeparation = 160;":
            "nodeSpacing = 100; treeSpacing = 160; levelSeparation = 240;",
        "        applyCurvedEdges();\n        network.fit();": (
            "        applyCurvedEdges();\n        network.fit();\n"
            "        if (mode === DEFAULT_LAYOUT && network.getScale() < 0.2) "
            f"focusDepthPath({js(central_paper)});"
        ),
        "  function _sugiyamaLayoutConfig(levelField) {": """
  function focusDepthPath(fallback) {
    const positions = network.getPositions();
    const links = edges.get();
    let best, width = Infinity;
    for (const first of links) {
      if (NODE_DETAILS[first.from]?.depth_level !== 0 ||
          NODE_DETAILS[first.to]?.depth_level !== 1) continue;
      for (const second of links) {
        if (second.from !== first.to || NODE_DETAILS[second.to]?.depth_level !== 2) continue;
        const [start, middle, end] = [first.from, first.to, second.to].map(id => positions[id]);
        if (!(start && middle && end)) continue;
        const left = Math.min(start.x, middle.x, end.x);
        const right = Math.max(start.x, middle.x, end.x);
        if (right - left < width) {
          width = right - left;
          best = {x: (left + right) / 2, y: middle.y};
        }
      }
    }
    if (best) network.moveTo({position: best, scale: 0.75, animation: false});
    else network.focus(fallback, {scale: 0.75, animation: false});
  }

  function _sugiyamaLayoutConfig(levelField) {""",
        "</style>": """
  html {scrollbar-gutter:stable;}
  #mynetwork {height: 72vh !important;}
  #citracer-legend, #citracer-legend-resize {position:absolute;}
  #citracer-info {position:relative; inset:auto; width:auto; max-height:none;
                  margin:12px; box-sizing:border-box; overflow-wrap:anywhere;}
  #citracer-info details {margin:8px 0;}
  #citracer-info blockquote {margin:6px 0; padding-left:10px; border-left:3px solid #ccc;}
  </style>""",
        """      network.on('hoverNode', params => {
        if (pinnedNodeId) return;
        showInfo(params.node);
      });""": "",
        "    currentNodeId = nodeId;": "    html += PAPER_EVIDENCE[nodeId] ?? '';\n    currentNodeId = nodeId;",
        "  const NODE_DETAILS =": f"  const PAPER_EVIDENCE = {js(node_evidence)};\n"
                                 f"  const EDGE_EVIDENCE = {js(edge_panels)};\n  const NODE_DETAILS =",
        "        if (!(params.nodes && params.nodes.length)) return;": """
        if (!params.nodes?.length) {
          const edge = params.edges?.length ? edges.get(params.edges[0]) : null;
          if (edge) {
            setPinned(null);
            currentNodeId = null;
            document.getElementById('citracer-info-body').innerHTML = EDGE_EVIDENCE[edge.from]?.[edge.to] ?? '';
            document.getElementById('citracer-info').style.display = 'block';
          }
          return;
        }""",
    }
    for before, after in rules.items():
        if before not in template:
            raise ValueError(f"Unexpected citracer overlay: {before}")
        template = template.replace(before, after, 1)
    return template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="피싱 탐지 인용망")
    args = parser.parse_args()
    graph, papers, pairs = make_payload(read_graph(args.input))
    metrics = analytics.analyze(graph)
    central_paper = max(papers, key=lambda node: metrics["node_metrics"][node]["betweenness"])
    max_centrality = metrics["node_metrics"][central_paper]["betweenness"]
    overlay = customized_overlay(papers, pairs, args.title, central_paper, max_centrality)

    class OfflineNetwork(visualizer.Network):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, cdn_resources="in_line")

        def write_html(self, name, local=True, notebook=False, open_browser=False):
            # PyVis uses the Windows locale when writing embedded Unicode assets.
            self.html = self.generate_html(name, local=local, notebook=notebook)
            Path(name).write_text(self.html, encoding="utf-8")
            if open_browser:
                import webbrowser
                webbrowser.open(Path(name).resolve().as_uri())

        def add_node(self, node_id, **kwargs):
            label = kwargs.get("label", "")
            if len(papers) > 150 and len(label) > 13:
                kwargs["label"] = label[:12].rstrip() + "…"
            super().add_node(node_id, **kwargs)

    palette = {
        "root": {"background": "#2563eb", "border": "#174db7"},
        "analyzed": {"background": "#008577", "border": "#00665b"},
        "no_match": {"background": "#a65316", "border": "#87400f"},
    }
    with patch.object(visualizer, "_load_overlay_template", return_value=overlay), \
         patch.object(visualizer, "Network", OfflineNetwork), \
         patch.dict(visualizer.STATUS_COLORS, palette):
        visualizer.render(graph, args.output, default_layout="sugiyama-depth", analytics=metrics)
    output = args.output.read_text(encoding="utf-8")
    output = re.sub(r'<link\b[^>]*\bhref="https?://[^"]+"[^>]*>', "", output)
    output = re.sub(r'<script\b[^>]*\bsrc="https?://[^"]+"[^>]*>\s*</script>', "", output)
    output = re.sub(r'<img\b[^>]*\bsrc="https?://[^"]+"[^>]*>', "", output)
    for label, role in (
        ("root", "R1 출발 논문"),
        ("analyzed (keyword found)", "R2 직접 인용"),
        ("analyzed (no match)", "R3 추가 인용"),
    ):
        output = output.replace(f"</span>{label}</div>", f"</span>{role}</div>", 1)
    args.output.write_text(output, encoding="utf-8")
    print(f"{len(graph.nodes)} nodes, {len(graph.edges)} directed pairs: {args.output}")
    print(f"Publication year present: {sum(node.year is not None for node in graph.nodes.values())}/{len(graph.nodes)}")


if __name__ == "__main__":
    main()
