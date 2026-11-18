# Windows PDF 인계 기반 피싱 논문 분석

2026-11-18 완료한 배치 `20261117T135121Z_phishing_detection`의 최종 공유 결과다.

## 산출물

- [최종 HTML](graph.html)을 내려받아 브라우저에서 연다.
- [표시 그래프 스냅샷](graph-snapshot.json)은 최종 HTML에서 추출한 노드·간선·중심성·근거 패널이다.
- [검증 요약](verification.json)은 Windows에서 확인한 수와 파일 해시, Ubuntu 검수 보고의 범위를 기록한다.
- [연구 보고 PPT](../../presentations/citation-report-20261118/research-report.pptx), [PPT 원본과 출처](../../presentations/citation-report-20261118/README.md)

| 항목 | 결과 |
| --- | ---: |
| Windows에서 검증해 인계한 PDF | 100편 |
| 선정한 R1 | 30편 |
| 고유 논문 노드 | 421개 |
| 고유 방향 간선 | 419개 |
| 대응하는 간선 근거 패널 | 419개 |
| 출판연도 확인 노드 | 170개 |
| 문맥 추출 기록이 없는 고립 R1 | 11편 |

문맥 분류는 소개 310, 보류 77, 비교·검증 22, 한계 지적 10, 채택·발전 0으로 합계 419개다. 동일 방향 쌍당 한 번 적용하며 매개중심성과 문맥 점수는 별도 표시한다. 채택 0건은 현재 자동 분류에서 확정된 건수다.

## 실행 흐름과 검수

Windows 수집기가 로그인된 Chrome의 기관 링크에서 PDF를 저장하고, `%PDF-`·크기·읽기 가능 여부·첫 페이지 제목 또는 DOI를 검사했다. 검증한 100편과 SHA-256 장부를 읽기 전용 `paper-inbox` 공유 폴더로 인계했다. Ubuntu가 해시를 대조해 새 분석 실행에 등록한 뒤 R1 선정, 전문 참고문헌과 문맥 추적, citracer 렌더링을 진행했다.

최종 원본 파일 이름은 `261118_0126latest.html`이며 SHA-256은 다음과 같다.

```text
8a079bf53040b1af5558134f80f261e245ed2ffd39b2f879dc82c479c1e7ea99
```

Windows에서 최종 HTML의 해시, 419개 고유 방향쌍, 419개 근거 패널, 끝점 존재, 자기간선 0개, R1 30개 보존과 출판연도를 검사했다. 잘린 `10.1016/j.comnet` 식별자는 미확인 로컬 참조로 보존하고 중심성을 다시 계산했다. 자기간선 1건은 표시와 점수 집계에서 제외하고 원시 근거는 VM 장부에 보존했다.

Hermes는 Ubuntu에서 레이아웃 안정화 후 실제 W3C 포인터로 노드와 R1→R2·R2→R3 간선을 클릭해 하단 근거 패널을 확인했다고 보고했다. 직선 표시로 검수한 뒤 기본 곡선 설정을 복원하고 외부 HTTP 요청 0건 및 공유본 해시 일치를 보고했다. Windows에서는 브라우저의 로컬 파일 접근 제한으로 독립 UI 재검수를 수행하지 못했다.

## 분석 한계

보류 77건과 고립 R1 11편의 문맥 추출 원인은 추가 검토가 필요하다. 추출 기록 0건은 실제 참고문헌이 없다는 의미로 사용하지 않는다. 자동 문맥 분류는 사람 검토와 정확도 평가가 남아 있다.

최고 매개 후보인 LLM 보안 리뷰에는 들어오는 간선 1개와 나가는 간선 104개가 있다. 수집 범위와 리뷰 논문의 참고문헌 폭이 순위에 영향을 준다. 해당 후보를 인용한 문장의 비교·검증 분류는 재검토 대상이다. [별도 검토](../../docs/llm-security-review-assessment-20261118.md)

## 백업 범위와 재개 위치

이번 Git 백업은 Windows 수집·인계·복구 코드, 범용 citracer 렌더러, 운영 규칙, 이 최종 HTML과 스냅샷·검증 요약, 발표 자료 및 제작 소스를 포함한다.

Ubuntu 분석 실행은 `research/paper-data/runs/cybersecurity/phishing_detection_windows_handoff_20261117T135121Z/`에 있다. 주요 장부는 다음과 같다.

- `status.json`
- `ledger/selected_r1.json`
- `ledger/ISOLATED_R1_REASONS.json`
- `ledger/FINAL_R1_COMPLETE_QA.json`
- `citation_trace/20261118T001021Z/citracer_context_graph_final_r1_complete/edge_pointer_verification.json`

이 VM에서 생성한 `trace_fulltext.py` 등 실행별 Python 스크립트와 원시 장부는 추가 회수가 필요하다. 이번 백업 시 SSH는 인증에 실패했고 Discord 연결은 재로그인을 요구했다. 위 경로를 최신 실행 코드의 재개 지점으로 보존한다. 저장된 그래프 스냅샷은 표시 상태를 재검토하는 자료이며 전체 추출 원장을 대체하지 않는다.

원문 PDF와 브라우저·인증 데이터는 공개 저장소에 포함하지 않는다.
