# 논문 인용망 연구 보고 발표

[12장 PPTX](research-report.pptx)는 NetMiner 스터디, 매개중심성 계산, 합의한 문맥 가감점, 실제 실행 화면과 최신 피싱 결과를 보고하는 자료다. 표와 본문은 편집 가능한 슬라이드 객체이며 발표자 노트에 출처를 기록했다.

화면 캡처는 이전 검수 실행의 실제 450노드·433인용 화면이다. 최신 2026-11-18 실행의 421노드·419간선은 별도 결과 슬라이드에 표시했다. 캡처의 기준 시점과 최신 실행을 구분한 상태로 발표한다.

## 원본과 재생성

- `build-report.mjs`는 슬라이드 구성과 발표자 노트다.
- `export.mjs`는 `@oai/artifact-tool`을 사용할 수 있는 Node 환경에서 PPTX를 생성한다.
- `results.json`은 최신 그래프에서 추출한 상위 매개 후보와 출판연도 집계다.
- `assets/`에는 실제 화면 캡처와 공식 KGU 로고가 있다.

Codex의 워크스페이스 의존성 도구로 Node 실행 파일과 `@oai/artifact-tool` 패키지 경로를 확인한다. 해당 패키지를 import할 수 있는 환경에서 다음을 실행한다. 출력 파일 경로를 주면 그 위치에 생성한다.

```text
node export.mjs ./research-report-regenerated.pptx
```

발표 자료는 Artifact Session에서 작성·렌더링 검수하고 PPTX로 내보냈다. 최종 파일은 12장, 발표자 노트 12개, 표 10개와 이미지 포함 여부·패키지 구조·레이아웃·폰트 선언·재import를 확인했다. Microsoft PowerPoint 앱에서 직접 열어 확인한 상태는 아니다.

## 출처와 권리

- NetMiner 공식 Methodology — https://www.netminer.com/kr/netminer/methodology.php
- citracer — https://github.com/marcpinet/citracer, MIT. 그래프 분석과 HTML 렌더링에 사용했다.
- NetworkX 매개중심성 — https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.betweenness_centrality.html
- OpenAI Codex — https://openai.com/codex/, 구현·오류 수정·검수 및 발표 자료 작성 지원에 활용했다.
- 문맥 배점 — [프로젝트 합의 규칙](../../skills/root-paper-research/CITATION_CONTEXT_RULES.md)
- KGU 로고 — [경기대학교 공식 UI](https://www.kyonggi.ac.kr/www/contents.do?key=5093), [원본 SVG](https://www.kyonggi.ac.kr/site/www/images/contents/key5093_img01_.svg)

공식 로고는 원본 SVG를 보존하고 슬라이드에는 동일한 색과 비율의 PNG 변환본을 넣었다. KGU 로고의 권리는 경기대학교 등 원 권리자에게 있으며 프로젝트의 MIT 라이선스와 별도로 취급한다.
