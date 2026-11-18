# 논문 수집·인용 분석

대학교 도서관 EDS에서 논문 후보를 수집하고, Windows에서 확보한 PDF를 Ubuntu의 Hermes에 인계해 인용 관계와 본문 근거를 분석하는 연구 파이프라인이다. citracer와 NetworkX로 방향성 매개중심성을 계산하고, 인용 간선을 선택하면 문맥 점수와 PDF 페이지를 보여준다. Hermes가 호출하는 MCP 검색·보존·PaperQA 도구도 함께 제공한다.

## 최신 실행 결과 · 2026-11-18

피싱 탐지 PDF **100편**을 Windows에서 검증한 뒤 읽기 전용 공유 폴더로 Ubuntu에 인계했다. 출발 논문 R1 **30편**을 선정하고 R2·R3 참고문헌을 추적해 **421노드·419방향 간선**의 최종 HTML을 공유했다.

| 항목 | 확인한 결과 |
| --- | --- |
| 인계 | PDF 100편의 해시·헤더·첫 페이지 제목 또는 DOI 검증 |
| 출발 논문 | R1 30편과 선정 이유 보존 |
| 인용 그래프 | 421노드, 고유 방향 간선 419개, 근거 패널 419개 |
| 출판연도 | 최종 그래프 421노드 중 170개 확인 |
| 문맥 분포 | 소개 310, 보류 77, 비교·검증 22, 한계 지적 10, 채택·발전 0 |
| 남은 분석 | 고립 R1 11편의 문맥 추출 원인, 보류 인용과 자동 분류의 사람 검토 |

- [최종 인터랙티브 그래프 HTML](reports/phishing_windows_handoff_20261118/graph.html)을 내려받아 브라우저에서 연다.
- [실행 결과와 검증 범위](reports/phishing_windows_handoff_20261118/README.md), [그래프 스냅샷 JSON](reports/phishing_windows_handoff_20261118/graph-snapshot.json), [검증 요약](reports/phishing_windows_handoff_20261118/verification.json)
- [12장 연구 보고 PPTX](presentations/citation-report-20261118/research-report.pptx), [발표 자료 원본과 출처](presentations/citation-report-20261118/README.md)
- [Windows PDF 인계 방법](tools/kyonggi-library-collector/README.md#windows에서-받은-pdf를-ubuntu로-인계), [그래프 화면 규칙](skills/root-paper-research/CITATION_GRAPH_RULES.md), [1사이클 실행 규칙](skills/root-paper-research/FULL_CYCLE_RULES.md)

최종 HTML의 파일 해시와 고유 간선·근거 패널·끝점·R1 보존을 Windows에서 확인했다. Ubuntu 실제 클릭 검수는 Hermes의 실행 보고로 확인했다. Windows 직접 UI 재검수와 문맥 분류 정확도 평가는 남아 있다. VM에서 새로 만든 전체 분석 실행 코드는 현재 원격 접속 인증이 필요해 이번 백업에 포함하지 못했다. 보존 범위는 실행 보고서에 기록했다.

## 연구 진행 현황

경기대 EDS와 공개 검색에서 후보를 수집하고, 선별 근거와 전문 확보 상태를 남긴다. 확보한 논문에서 R1 출발 논문 → R2 직접 인용 → R3 한 단계 추가 인용을 추적한다. 연구 질문은 **어떤 논문이 방법의 기반을 만들고, 발전시키고, 서로 다른 연구 흐름을 연결하는가**다. 인용망에서 후보를 찾고 실제 인용 문맥으로 역할을 검토한다.

- [전체 구조 PDF](docs/paper-architecture-bw.pdf)
- [랜섬웨어 후보 선정 근거와 중간 논문 분석](docs/ransomware-citation-study.md)
- [NetMiner에 가져올 랜섬웨어 인용망과 재현 방법](examples/ransomware-netminer/README.md)
- [citracer로 피싱 논문 인용 문맥을 추적한 실험](examples/citracer-phishing/README.md)
- [헤르메스 인용 문맥 채점 규칙과 적용 상태](skills/root-paper-research/CITATION_CONTEXT_RULES.md)

## 포함 기능

- `collect_top_venue_papers`: ACL Anthology·OpenReview의 공식 합격 논문 색인에서 AI 후보를 수집하고, BK21+ 2018 판본의 원래 등급과 논문 유형 적용 상태를 별도로 기록. 현재 1차 구현은 ACL·EMNLP·NAACL·ICLR·ICML·NeurIPS이며 보안 학회 수집기는 후속 단계.
- `research_search`: 트랙별 검색식·UTC 시각·원 응답 저장. 현재 검색 공급자는 Semantic Scholar이며 arXiv 통합 검색은 노출하지 않음.
- `trace_root_papers`: 참고문헌 최대 3단계, 중복·순환 처리, 출발 논문별 경로, 공통 루트 후보 순서화. 품질 점수 아님.
- `download_root_pdf`: 지정 공개 호스트 PDF 다운로드·SHA-256. 로그인·압축파일·코드 실행 없음.
- `preserve_pdf`: inbox의 합법적으로 확보한 PDF를 원본 보존하며 등록.
- `record_review`: 포함/제외 이유·공식 게재 근거·BK21 기준선·루트 판정 이유를 검토자 진술로 저장.
- `analyze_root_paper`: 명시한 모델/임베딩으로 PaperQA 분석, 근거 구절·원문 위치와 초안 보존. 모델 처리 허용 전에는 실행 안 함.

`runs/ai`, `runs/cybersecurity` 아래 실행마다 새 폴더 생성. 기존 결과를 수정하지 않는다. 검색과 공식 검증, DB 인용과 원문 인용 맥락, 후보와 확정 판정을 구분한다.

## 경기대 도서관 구독 DB 병행 탐색

논문 분석 키워드마다 공개 검색과 경기대 도서관이 제공하는 구독 DB 탐색을 함께 수행한다. 탐색마다 **DB명·정확한 검색식·확인 시각·결과 수**를 기록하고, 논문 접근 상태는 아래 네 가지로 구분한다.

- `공개 전문`
- `기관 구독 전문 확인`
- `메타데이터만 확인`
- `기관 구독 필요·미확보`

도서관 보조 수집기는 EDS 검색과 로그인된 브라우저의 기관 링크를 이용한다. 계정 소유자가 로컬 브라우저에서 로그인한 뒤, 같은 브라우저가 표시하는 PDF를 저장하고 신원을 검증한다. 브라우저 프로필은 계정 소유자의 컴퓨터에 유지하며 자격증명·쿠키·인증 헤더와 원문 PDF는 Git에 포함하지 않는다.

## 인용 그래프 HTML과 이관 백업 자료

VirtualBox→VMware 이관 자료는 [`vm-migration-backup-20260928/`](vm-migration-backup-20260928/)에 보관한다.

- [이관 범위·제외 목록·복원 절차](MIGRATION_BACKUP.md)
- [검수 가능한 인용 그래프 입력 JSON](vm-migration-backup-20260928/graph-renderer/graphs/graph-output/graph.json)
- [기본 로컬 HTML 그래프](vm-migration-backup-20260928/graph-renderer/graphs/graph_ui_test_20260923T060000Z/site/index.html)
- [향상 로컬 HTML 그래프](vm-migration-backup-20260928/graph-renderer/graphs/graph_ui_enhanced_test_20260924T084500Z/site/index.html)
- [향상 그래프 UI 실제 검수 결과](vm-migration-backup-20260928/graph-renderer/graphs/graph_ui_enhanced_test_20260924T084500Z/RESULT.md)

향상 HTML은 제목·저자·논문 ID 검색, 원문 참고문헌/메타데이터 간선 필터, 노드 클릭 시 인접 인용선 강조, 우측 인용 연결·근거 패널, 노드 ID와 `미기록` 표기를 제공한다. 그래프는 입력 `graph.json`을 읽기 전용으로 사용하며, 외부 URL 요청 없이 로컬 정적 HTML로 검수했다. 포함된 결과는 랜섬웨어 통합 run의 **작은 그래프 JSON·HTML·검수 기록**이고, 대용량 원문 PDF·원시 메타데이터·세션은 포함하지 않는다.

## ransomware detection 소형 1사이클 드라이런

정식 100편 실험 전, R1 5편 → 최종 1편 → 인용 근거가 확인된 R2 2편으로 제한해 검색·후보 선정·인용 추적·클릭형 그래프 검수를 완료한 공개 번들이다. 그래프는 기본 일반 선, 노드 클릭 시 인접 `인용한 → 인용된` 화살촉, `☰ R1 전체 후보` 제목 메뉴, 메타데이터 한계가 적힌 분석 메모를 제공한다. 경기대 도서관은 이번에는 **비로그인 공개 메타데이터만** 확인했다. 장부·검증·이식 가능한 예시 HTML·다음 정식 실행 조건은 [`reports/ransomware_detection_dryrun_20260929/`](reports/ransomware_detection_dryrun_20260929/)에 있다.

## 로컬 실행

Python 3.11 이상. 이 Windows 프로젝트에는 `.venv`를 별도로 구성했다. 다른 서버로 옮길 때 `.venv`는 복사하지 말고 새로 만든다. 아래 명령은 운영자가 검토 후 직접 수행하는 설치 절차이며 논문 코드 실행 명령이 아니다.

```bash
python -m venv .venv
# Linux: .venv/bin/python / Windows: .venv\Scripts\python.exe
.venv/bin/python -m pip install -e '.[analysis]'
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/smoke_mcp.py
.venv/bin/python -m root_paper_lab.server
```

마지막 명령은 stdio MCP 서버이므로 일반 채팅 입력을 받지 않는다. 헤르메스의 MCP 클라이언트가 시작해야 한다. 실제 실행 호스트·Hermes 버전을 확인하고 공식 MCP 연결 절차로 등록한다. 기존 봇/관리자/로그인 설정은 이 프로젝트에서 바꾸지 않는다.

서버 실행 명세: command는 해당 가상환경 Python의 절대 경로, args는 `-m root_paper_lab.server`. 선택 환경변수 `ROOT_PAPER_DATA`는 결과 저장 폴더, `ROOT_PAPER_IMPORT`는 PDF 입력 폴더다. 기본값은 프로젝트의 runs, inbox다. 비밀정보는 이 파일이나 MCP 호출 인자에 넣지 않는다.

### 기관 구독 원문 가져오기

기관 접근이 필요한 후보는 계정 소유자가 로그인한 브라우저에서 연다. `auto-downloads`는 후보를 한 편씩 처리하며, 표시된 PDF를 저장한 뒤 제목·DOI와 파일 상태를 검사하고 실패 사유를 장부에 남긴다. `pdf_handoff.py stage`는 검증한 PDF와 SHA-256 장부를 하나의 인계 배치로 만들고, Ubuntu에서 `verify`로 다시 대조한다. 그 뒤 `preserve_pdf` 또는 해당 분석 실행의 입력 등록 단계로 연결한다.

### 경기대 도서관 보조 수집기

`tools/kyonggi-library-collector/`에는 이 연구 흐름의 **로컬 보조 수집기**를 함께 보관한다. 역할은 다음과 같이 분리한다.

- `kyonggi_collector.py collect`: 경기대 EDS 공개 검색에서 키워드별 서지 메타데이터·DOI·원문 연결 주소를 최대 지정 건수만큼 장부로 수집한다.
- `local_research_pipeline.py`: 중복 제거, 로컬 점수화·후보 선별, 확보한 PDF의 텍스트/참고문헌 추출, 근거 기반 인용 그래프 생성을 LLM 호출 없이 수행한다.
- 기관 구독 원문은 계정 소유자가 로그인한 합법적 세션에서만 열람한다. 자격증명·쿠키·세션값은 저장소, 결과 장부, Git 기록에 넣지 않는다.

2026-11-18까지 Windows에서 피싱 탐지 PDF 100편을 확보·검증하고 Ubuntu로 인계한 실행을 완료했다. 수집기는 기존 Chrome 연결, IEEE PDF 뷰어 응답 저장, 파일 신원 검증, 장부 기반 재개와 목표 건수 종료를 지원한다. 이 결과는 해당 배치와 제공자 경로에서 확인한 범위다. 다른 제공자와 로그인 만료 상황은 실행 장부로 확인한다. 세부 명령은 [수집기 README](tools/kyonggi-library-collector/README.md), 이전 개발 과정은 [2026-10-06 운영 기록](docs/kyonggi-library-collector-20261006.md)을 참조한다.

## 매개중심성과 인용 문맥

NetMiner 실습에서 매개중심성과 중간 논문 해석을 공부하고, 프로젝트의 계산과 HTML 렌더링에는 [citracer](https://github.com/marcpinet/citracer)와 NetworkX를 사용했다. 기본 배치는 위에서 아래로 R1·R2·R3를 표시하는 Sugiyama 깊이순이다. 연도순 전환과 제목 검색을 제공하며, 논문 및 선택한 간선의 근거는 그래프 아래에 표시한다.

| 인용 목적 | 문맥 점수 |
| --- | ---: |
| 방법 채택·발전 | +1.5 |
| 배경·단순 소개 | +0.5 |
| 비교·검증 | +0.5 |
| 한계 지적 | −0.5 |
| 판정 보류 | +0.2 |

같은 방향 논문 쌍에 한 번 적용하고 채택 근거를 우선한다. 이 배점은 프로젝트에서 합의한 규칙이다. 매개중심성과 문맥 점수는 각각 표시하며, 합산 순위의 공식은 아직 정하지 않았다. 원문의 인용 문장·주변 문맥·PDF 페이지와 판단 이유를 함께 검토한다.

현재 표본의 최고 매개 후보는 *Large Language Models for Cyber Security: A Systematic Literature Review*다. 이 노드로 들어오는 인용은 1개, 나가는 인용은 104개로, 리뷰 논문의 범위와 수집된 그래프가 순위에 영향을 준다. [후보 논문 검토와 분류 재검토 사항](docs/llm-security-review-assessment-20261118.md)을 함께 확인한다.

## 운영 복구

`python scripts/recover_hermes_discord.py`는 Windows에서 관리자 권한으로 VMware NAT 서비스를 재시작한다. Ubuntu에서는 Discord API 연결을 먼저 확인하고 `hermes-gateway` 사용자 서비스를 재시작한다. [복구 스크립트](scripts/recover_hermes_discord.py)의 `--help`로 실행 범위를 확인한다.

운영 규칙은 `skills/root-paper-research/SKILL.md`다. 확인된 Hermes 스킬 설치 위치에 복사하되 같은 이름이 있으면 덮어쓰지 말고 비교한다. 2026-09-14 Hermes 등록·Gateway 재시작·7개 도구 연결과 실제 수집 호출을 확인했다. 운영 검증의 출처와 한계는 `docs/operations-20260914.md`를 참조한다.

운영에서는 `ROOT_PAPER_DATA`를 코드 checkout 밖의 고정 절대경로로 지정한다. 프로그램을 업데이트해도 이 경로를 유지하고, 재시작 후 실제 프로세스의 환경변수와 반환된 run 경로를 함께 확인한다. 연구 보고의 상세 출력·다단계 추적 요구사항은 `docs/research-report-requirements.md`에 기록했다.

## 사용 예

디스코드에서: “AI 트랙에서 2024~2026년 ACL, EMNLP, ICML, NeurIPS의 agent security 관련 공식 게재 논문을 모아줘. BK21+ 2018 기준과 논문 유형을 분리해서 표시하고 최대 20편만 후보로 저장해줘.”

디스코드에서: “사이버보안 트랙으로 DNS 터널링 탐지 논문 후보를 찾아줘. 공식 게재를 검토해 출발 논문 3편을 정하고, 깊이 2에서 공통 루트논문 후보를 찾아줘. PDF는 보존하고 분석 모델·비용을 확인한 다음 1편만 PaperQA로 분석해줘.”

DNS는 기능 사용 예시이며 확정 연구 주제가 아니다. 검색 키워드는 공개 검색 서비스로 전달되므로 비공개 연구 내용·비밀을 넣지 않는다.

## 검증 경계

자동화된 것은 검색·참고문헌 그래프·PDF 보존·분석 호출이다. 공식 proceedings 직접 확인과 원천성 최종 판정은 Hermes/사람이 근거를 보고 수행한다. 리뷰 도구는 입력 근거를 저장할 뿐 독립적인 사실검증기가 아니다. 루트 후보가 모든 참고문헌의 절대적인 시발점이라는 주장은 하지 않는다.

다운로드 허용 호스트: arxiv.org, export.arxiv.org, proceedings.mlr.press, usenix.org, www.usenix.org, aclanthology.org, openreview.net, papers.neurips.cc, proceedings.neurips.cc. 그 외는 로컬 PDF로 가져온다. DOI가 연결돼도 PDF를 확보하지 못할 수 있다.

설치 성공·모의 테스트 성공과 실제 검색/유료 모델 분석/디스코드 연동 성공을 구분한다. 현재 검증 내역은 `VALIDATION.md` 참조.

## 라이선스

프로젝트 자체 코드와 문서는 [MIT 라이선스](LICENSE)를 따른다. 포함된 외부 코드의 라이선스와 출처는 [외부 코드 고지](THIRD_PARTY_NOTICES.md)를 참조한다.

KGU 로고는 경기대학교 공식 UI 자료이며 권리는 원 권리자에게 있다. 발표 자료에 원본 색과 비율을 유지해 삽입했다. OpenAI Codex는 프로젝트 구현·오류 수정·검수와 발표 자료 작성 지원에 활용했다. 도구의 활용 범위와 링크는 발표 자료의 출처 및 노트에 기록했다.

## 원본

- AI Research Trend Atlas: https://github.com/LikeACloud7/ai-trend — commit `e20dfc1eebff33c0ce635f26be70cce82ae6bacd`, MIT. 공식 ACL Anthology/OpenReview 수집 구조를 참고해 Python·감사기록·BK21 분리 판정 방식으로 수정. 자세한 내용은 `THIRD_PARTY_NOTICES.md`.
- Scholar Search MCP: https://github.com/Silung/scholar-search-mcp — commit `1392e7e6f483bb2fdbef42e37610b82620612ee7`, MIT, 원본은 vendor에 보존.
- PaperQA: https://github.com/Future-House/paper-qa — tag `v2026.08.12`, commit `57e89f7223b0960d5ee5ea048c69e3c47e088572`, Apache-2.0, 원본은 vendor에 보존. 실행용 패키지는 고정 버전 설치.
- Hermes MCP: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/

원본 Scholar의 동일 arXiv 소스 폴더 삭제·압축 해제 도구는 노출하지 않는다. vendor 원본을 별도로 실행하면 그 보호가 적용되지 않으므로 이 facade만 연결한다.
