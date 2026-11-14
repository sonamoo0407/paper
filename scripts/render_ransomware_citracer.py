"""Render the archived ransomware citation ledger with citracer."""
import json
from html import escape
from pathlib import Path

from citracer import analytics, visualizer
from citracer.models import CitationEdge, PaperNode, TracerGraph

root = Path(__file__).resolve().parents[1]
out = root / "docs"
source = root / "vm-migration-backup-20260928/graph-renderer/graphs/graph-output/graph.json"
data = json.loads(source.read_text(encoding="utf-8"))
graph = TracerGraph()
for row in data["nodes"]:
    graph.add_node(PaperNode(row["id"], row["title"], year=row.get("year"),
                            depth=int(row["id"][1]) - 1, status="pending"))
for row in data["edges"]:
    evidence = [item for r in row["records"] if r["verification"] == "fulltext"
                for item in r["evidence"]]
    if evidence:
        graph.add_edge(CitationEdge(row["source"], row["target"],
                                   context=" / ".join(evidence)))

metrics = analytics.analyze(graph)
assert (len(graph.nodes), len(graph.edges)) == (10, 14)
ranked = sorted(metrics["node_metrics"].items(), key=lambda kv: -kv[1]["betweenness"])
positive = [(pid, m["betweenness"]) for pid, m in ranked if m["betweenness"] > 0]
assert [pid for pid, _ in positive] == ["R2-01", "R2-02", "R2-03"]
metrics["timeline"] = []  # Imported ledger has no keyword matching data.

stage_colors = {"R1": "#2563eb", "R2": "#008577", "R3": "#a65316"}
legend = '<p><strong>노드 색:</strong> ' + " / ".join(
    f'<span style="color:{color}">●</span> {stage} {label}'
    for (stage, color), label in zip(stage_colors.items(), ["출발 논문", "직접 인용", "한 단계 더 추적"])
) + '</p><p>색은 인용 단계, 점 크기는 매개중심성입니다.</p>'

class StageNetwork(visualizer.Network):
    def add_node(self, node_id, **kwargs):
        color = stage_colors[node_id.split("-")[0]]
        kwargs["color"] = {"background": color, "border": color}
        super().add_node(node_id, **kwargs)

ranking = '<h3>중간 논문 후보 순위</h3><ol>' + "".join(
    f'<li>{escape(graph.nodes[pid].title.split(":")[0])} <b>{score:.5f}</b></li>'
    for pid, score in positive
) + '</ol><p>구조상 매개 후보이며 본문 의미는 별도 확인이 필요합니다.</p>'
report_link = '<p><a href="ransomware-citation-study.md">상세 보고서: 선정 이유 · 인용 근거 · 분석 파일 위치</a></p>'
seed_rows = [r for r in data["nodes"] if r["role"] == "starting"]
assert len(seed_rows) == 5
selection_reasons = {
    "R1-01": "탐지 · 인공 사용자 환경에서 랜섬웨어가 사용자 데이터와 상호작용하는 방식을 동적으로 분석한다.",
    "R1-02": "피해·복구 · 실제 대학 랜섬웨어 사고의 기술적 비용, 생산성 손실, 사회적 비용을 분석한다.",
    "R1-03": "탐지 · I/O 모니터링의 비용 문제를 다단계 탐지 방식으로 다룬다.",
    "R1-04": "탐지·복구 · 클라우드 블록 스토리지에서 탐지와 스냅샷 기반 데이터 손실 완화를 결합한다.",
    "R1-05": "공격 흐름·데이터셋 · 장기간 랜섬웨어 공격 환경을 세분화한 데이터셋으로 연구한다.",
}
assert selection_reasons.keys() == {r["id"] for r in seed_rows}
node_evidence = {}
for pid in graph.nodes:
    refs = [
        f'<li>{escape(e.source_id)} → {escape(e.target_id)}<br>{escape(e.context)}</li>'
        for e in graph.edges if pid in (e.source_id, e.target_id)
    ]
    node_evidence[pid] = (
        f'<h4>{escape(pid)} · 보존 인용망</h4>'
        + (f'<p>{escape(selection_reasons[pid])}</p>' if pid in selection_reasons else '')
        + '<h4>연결 및 원장 근거</h4>'
        + ('<ul>' + "".join(refs) + '</ul>' if refs else '<p>이 인용망에 연결 근거 없음</p>')
    )
node_evidence_json = json.dumps(node_evidence, ensure_ascii=False).replace("<", "\\u003c")
template = visualizer._load_overlay_template()
for before, after in {
    '<div>keyword: {{KEYWORD_CHIPS}}</div>': '<div>랜섬웨어 보존 인용망 · 원문 확인 간선 14개</div>' + ranking + report_link,
    '    currentNodeId = nodeId;': f'    html += ({node_evidence_json})[nodeId] || "";\n    currentNodeId = nodeId;',
    'nodes (click to toggle)</div>\n{{LEGEND_ROWS}}': '인용 단계</div>\n' + legend,
    'value="in-degree" selected': 'value="in-degree"',
    'value="betweenness">betweenness': 'value="betweenness" selected>매개중심성',
    'let currentSizeMode = "in-degree";': 'let currentSizeMode = "betweenness";',
    '>node size</label>': '>논문 점 크기</label>',
    '>in-graph citations</option>': '>그래프 내 피인용 수</option>',
    '>search</label>': '>검색</label>',
    'placeholder="title, author…"': 'placeholder="제목…" ',
    '>Analytics</summary>': '>그래프 지표</summary>',
    "'Betweenness: '": "'매개중심성: '",
    "escapeHtml(d.status)": "escapeHtml(d.status === 'pending' ? '보존 인용망에서 가져옴' : d.status)",
}.items():
    assert before in template, before
    template = template.replace(before, after)
visualizer._load_overlay_template = lambda: template
visualizer.Network = StageNetwork
html_path = out / "ransomware-citracer.html"
visualizer.render(graph, html_path, analytics=metrics)
html = html_path.read_text(encoding="utf-8")
html_path.write_text("\n".join(line.rstrip() for line in html.splitlines()) + "\n", encoding="utf-8")
