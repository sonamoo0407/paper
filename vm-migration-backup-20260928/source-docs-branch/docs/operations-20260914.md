# 운영 검증 기록 — 2026-09-14

## 근거 범위

Codex가 Discord의 Hermes에 요청을 전달하고 도구 호출 및 결과 보고를 확인했다. 서버 파일 검사는 Hermes가 수행했다. Codex의 직접 SSH 인증은 실패했으며 직접 서버 검증으로 표현하지 않는다. 인증정보와 서버 설정 원본은 이 저장소에 보관하지 않는다.

## 확인한 운영 상태

- 운영 코드: 커밋 `aef47b4503f9ed31765b81e0d9043f1e14cd6768`의 분리 checkout.
- staging 설치 검증: 테스트 18개, stdio MCP handshake, PaperQA import/API 호환성 검사 통과 보고.
- Gateway 재시작 성공 메시지와 실제 MCP 도구 7개 노출 확인.
- 도구: research_search, collect_top_venue_papers, trace_root_papers, preserve_pdf, download_root_pdf, record_review, analyze_root_paper.
- 최초 전환 시험은 새 코드를 실행했지만 기존 ROOT_PAPER_DATA 때문에 이전 결과 폴더에 저장됨.
- 설정의 ROOT_PAPER_DATA만 코드와 분리된 고정 데이터 경로로 수정. 시각이 포함된 설정 백업과 권한·소유권 보존, 다른 설정 불변 비교 완료 보고.
- Discord `/restart` 후 실제 프로세스의 데이터 경로 일치 확인 보고.
- ACL 2025, query=agent security, max_results=1 실제 수집 1회 성공. 후보: G-Safeguard.
- 새 결과: `${RESEARCH_DATA}/ai/20260914T100608-04f16f42e517`.
- request.json, venue-search.json, sources/acl-2025.html, events 파일 존재 확인 보고.
- 기존 결과는 원래 위치에 보존. 이번 수정은 서버 운영 설정 변경이며 프로그램 로직 변경은 없음.

`${RESEARCH_DATA}`는 ROOT_PAPER_DATA로 지정한 절대경로다. 배포 경로·설정 백업의 실제 위치는 사용자의 비공개 작업 기록에 보관한다.

## 후속 연구 상태

이후 Discord에서 MITRE ATT&CK 출발 논문 5편 PDF 보존과 제한된 참고문헌 그래프 탐색을 수행했다는 Hermes 보고를 확인했다. 5편은 검색 단계의 출발 논문이며 95편은 그 뒤 발견된 루트 후보다. 95편 중 최종 5편을 확정한 결과가 아니다.

최초 그래프는 깊이 2, 최대 노드 100의 제한 탐색이다. 조회 실패 0건이어도 완전탐색이나 원천성 검증 완료를 뜻하지 않는다. 후속 다단계 탐색 및 원문 인용 문맥 검증은 완료 여부를 개별 보고서에서 구분한다.

PaperQA 실제 모델 분석은 아직 미실행이다. 여러 모델의 독립 분석·교차 검토는 설계 논의 단계이며 구현·운영 완료로 취급하지 않는다. 학교 도서관 원문 가져오기 연계도 제안 단계다.

## 업데이트 절차

1. 코드 버전과 기존 설정의 비밀값 없는 구조를 확인한다.
2. 설정 변경 시 기존 권한을 유지한 시각 백업을 만든다.
3. 코드 실행 경로를 바꿔도 ROOT_PAPER_DATA는 유지한다.
4. Gateway를 지원되는 외부 재시작 경로로 재시작한다.
5. 실제 프로세스와 데이터 경로를 먼저 확인한 뒤 작은 실제 호출로 저장을 검증한다.
6. 기존 결과를 이동하거나 삭제하지 않는다. 필요 시 별도 이관 계획과 파일 무결성 비교를 수행한다.
