# 실행 계약

설계 참고: https://github.com/watericetangcw/academic-research-graph
원본 커밋: 4ac7b913821b5fdf4c1b11bd1025eb8f2f779b23
원본은 external/academic-research-graph에 별도 보존했다. 후보/근거 검토 그래프 분리와 증거 보존 설계를 참고한 별도 구현이다. 원본 코드나 렌더러를 복제하지 않았으며 공식 통합판이 아니다.

기존 원장에서 확인된 인용만 입력한다. semantic 관계를 인용으로 자동 변환하지 않는다.
```json
{"nodes":[{"id":"A","title":"출발 논문"},{"id":"B","title":"선행 논문"}],"seeds":["A"],"edges":[{"source":"A","target":"B","kind":"citation","verification":"fulltext","evidence":["A.pdf 참고문헌 3번"]}]}
```

전용 Python 환경(이번 설치에서 검증한 경로)으로 실행한다:
```bash
PYTHON=/home/sonamoo0407/research/venvs/paper-citation-graph/bin/python
$PYTHON scripts/build_forest.py citation-input.json --out runs/new-graph
$PYTHON scripts/test_forest.py -v
```
이 절의 절대 경로는 이번 로컬 설치 기록이다. 다른 환경에서는 같은 전용 venv의 실제 Python 경로로 바꿔 기록한다.

출력: input.json(원본), graph.json(근거와 집계), citations.graphml(방향 있는 전체 인용), backbone.graphml(무방향 신장 forest). 출력 폴더가 존재하면 중단한다. 네트워크/모델 호출은 없다.

무방향 투영의 최대 신장 포리스트를 계산한다. 가중치 원문 확인=2, 메타데이터=1은 표시용 근거 우선순위이며 논문 품질이 아니다. 동점은 정렬된 ID와 간선 순서를 사용한다. 반대 방향 인용은 투영에서 묶지만 전체 원장에는 둘 다 남긴다. 고립 노드 보존, 연결 안 된 부분에 가짜 간선 추가 금지.

evidence는 존재만 검사하므로 실제 출처 검증은 Hermes와 작업자가 해야 한다. 불확실한 간선은 excluded_edges에 남긴다. 입력 누락 노드는 오류 처리한다. 제목 동일성만으로 ID 병합하지 않는다.

현재 계산기와 GraphML 출력까지 구현했다. Academic Research Graph 클릭형 HTML 렌더러 연결과 한국어 UI 이식은 미완료다. 기존 렌더러가 있으면 두 뷰를 구분해 시각화하되 렌더링 검증 전 그림 생성 완료라고 보고하지 않는다. 기존 20~30편·탑티어 우선·사람 검토 기준을 유지한다.
