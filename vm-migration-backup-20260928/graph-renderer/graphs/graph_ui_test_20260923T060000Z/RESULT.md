# 독립 로컬 그래프 UI 시험 결과

- 상태: **PASS**
- 입력: `../../graph-output/graph.json` (읽기 전용)
- HTML: `site/index.html`
- 화면 검수: `hover_click_screen.png`
- 자동 검수: `ui_test_result.json`, `webdriver_test.log`

## 실제 UI 검수

- R2-01 ShieldFS에서 WebDriver 호버 1회: 제목, 저자(`확인 불가/미기록`), 연도, 학회/저널(`확인 불가/미기록`), 한 줄 요약 표시 확인.
- 같은 R2-01에서 WebDriver 클릭 1회: 선정 이유, 검토 상태, 직접/간접 관계, 원문 근거, 원문 링크(`확인 불가/미기록`) 표시 확인.
- 최종 화면 PNG에서 툴팁과 전체 상세 패널을 시각 검수했고, 주요 텍스트 잘림·겹침은 발견하지 못함.

## 외부 요청 경계

- HTML은 외부 스크립트·CSS·폰트·이미지 URL을 참조하지 않는다.
- 실제 페이지 `performance` 자원 기록: 로컬 `http://127.0.0.1:18767/favicon.ico` 1건뿐.
- 외부 URL 요청: 0건.

## 메타데이터 경계

`graph.json`에 없는 저자, 학회/저널, 선정 이유, 원문 URL은 보완 검색하지 않고 `확인 불가/미기록`으로 표시했다.
