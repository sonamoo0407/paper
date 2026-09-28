# 루트논문 연구 도구 (초기 구현)

Hermes Agent가 자연어 요청을 해석하고, 이 프로그램의 MCP 도구를 호출하는 구조다. Scholar Search MCP의 검토한 Semantic Scholar 클라이언트를 재사용하며 페이지 순회·실행 기록을 보강했다. PaperQA로 보존 PDF의 근거 기반 분석 초안을 만든다. 독립적인 채팅 UI나 디스코드 봇은 만들지 않는다.

## 포함 기능

- `collect_top_venue_papers`: ACL Anthology·OpenReview의 공식 합격 논문 색인에서 AI 후보를 수집하고, BK21+ 2018 판본의 원래 등급과 논문 유형 적용 상태를 별도로 기록. 현재 1차 구현은 ACL·EMNLP·NAACL·ICLR·ICML·NeurIPS이며 보안 학회 수집기는 후속 단계.
- `research_search`: 트랙별 검색식·UTC 시각·원 응답 저장. 현재 검색 공급자는 Semantic Scholar이며 arXiv 통합 검색은 노출하지 않음.
- `trace_root_papers`: 참고문헌 최대 3단계, 중복·순환 처리, 출발 논문별 경로, 공통 루트 후보 순서화. 품질 점수 아님.
- `download_root_pdf`: 지정 공개 호스트 PDF 다운로드·SHA-256. 로그인·압축파일·코드 실행 없음.
- `preserve_pdf`: inbox의 합법적으로 확보한 PDF를 원본 보존하며 등록.
- `record_review`: 포함/제외 이유·공식 게재 근거·BK21 기준선·루트 판정 이유를 검토자 진술로 저장.
- `analyze_root_paper`: 명시한 모델/임베딩으로 PaperQA 분석, 근거 구절·원문 위치와 초안 보존. 모델 처리 허용 전에는 실행 안 함.

`runs/ai`, `runs/cybersecurity` 아래 실행마다 새 폴더 생성. 기존 결과를 수정하지 않는다. 검색과 공식 검증, DB 인용과 원문 인용 맥락, 후보와 확정 판정을 구분한다.

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

## 원본

- AI Research Trend Atlas: https://github.com/LikeACloud7/ai-trend — commit `e20dfc1eebff33c0ce635f26be70cce82ae6bacd`, MIT. 공식 ACL Anthology/OpenReview 수집 구조를 참고해 Python·감사기록·BK21 분리 판정 방식으로 수정. 자세한 내용은 `THIRD_PARTY_NOTICES.md`.
- Scholar Search MCP: https://github.com/Silung/scholar-search-mcp — commit `1392e7e6f483bb2fdbef42e37610b82620612ee7`, MIT, 원본은 vendor에 보존.
- PaperQA: https://github.com/Future-House/paper-qa — tag `v2026.08.12`, commit `57e89f7223b0960d5ee5ea048c69e3c47e088572`, Apache-2.0, 원본은 vendor에 보존. 실행용 패키지는 고정 버전 설치.
- Hermes MCP: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/

원본 Scholar의 동일 arXiv 소스 폴더 삭제·압축 해제 도구는 노출하지 않는다. vendor 원본을 별도로 실행하면 그 보호가 적용되지 않으므로 이 facade만 연결한다.
