# 향상 HTML 인용 그래프 렌더러 시험

## 상태

**PASS**

- 입력은 기존 `../../graph-output/graph.json` 읽기 전용으로 사용했다.
- 입력 SHA-256은 시험 전후 동일하다: `360315046b7eb75080fc7fa13b73c145de4eadaa108b3bf26bc369dbced37ccf`.
- 기존 그래프 산출물은 덮어쓰지 않았고, 이 폴더에만 새 파일을 만들었다.

## 기능 검수

- 제목·저자·논문 ID 검색: 실제 WebDriver 입력 `ShieldFS` 후 10개 중 1개 노드 표시 확인.
- 간선 필터: 원문 참고문헌 확인 간선은 입력상 14개, 메타데이터 확인 간선은 0개임을 확인.
- 실제 노드 클릭: R2-01을 클릭한 뒤 선택 ID `R2-01`, 인접 인용선 강조 4개, 우측 인용 연결 및 원문 근거 목록을 확인.
- 노드에는 ID와 연도를 표시.
- 입력 원장에 없는 저자·학회/저널·전문 상태·탑티어 상태·원문 URL은 모두 `미기록`으로 표시했고 보완 추정·검색은 하지 않았다.

## 네트워크 경계

- 외부 스크립트·CSS·폰트·이미지는 사용하지 않았다.
- WebDriver `performance` 기록에서 외부 URL 요청은 0건이다.
- 로컬 서버 및 WebDriver 종료 후 `127.0.0.1:18768`, `127.0.0.1:4448` 포트 종료를 별도 확인한다.

## 파일

- HTML: `site/index.html`
- 자동 검수: `ui_verification.json`, `ui_verification.log`
- 실제 브라우저 스크린샷: `enhanced_graph_ui.png`
- 입력 보존 해시: `input_graph_sha256_before.txt`, `input_graph_sha256_after.txt`
