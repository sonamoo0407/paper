# MITRE ATT&CK 연구: 출발 논문과 루트 추적 공개 요약

- 작성일: 2026-09-14
- 범위: 공개 PDF 5편과 참고문헌 역추적 기록의 공개용 분석 요약
- 데이터 경로 표기: `${RESEARCH_DATA}/cybersecurity/...` (`RESEARCH_DATA`는 `ROOT_PAPER_DATA`로 지정한 실행 결과 루트)
- 안전 경계: 출판된 원문 PDF, 원문 HTML, 검색 API 원응답, 환경 설정·인증 정보는 이 문서와 함께 공개하지 않는다.

## 핵심 구분

이번 기록에는 서로 다른 두 집합이 있다.

- **출발 논문 5편:** ATT&CK 연구 지형, 실제 탐지 coverage, LLM 기반 SIEM 규칙 매핑을 함께 보기 위해 먼저 고른 공개 PDF다.
- **루트 후보 95편:** 이 5편에서 참고문헌을 최대 2단계 역방향으로 따라가며 데이터베이스 관계에서 나온 이전 연구·공식 자료 후보다.

따라서 95편 가운데 최종 5편을 확정한 상태는 아니다. 95편은 `후보`이며, 원천성·직접 영향·인용 문맥은 별도 확인이 필요하다.

## 출발 논문 5편과 선정 이유

1. **SoK: The MITRE ATT&CK Framework in Research and Practice**
   - 역할: ATT&CK 활용을 CTI, 탐지, 위험평가, 레드/퍼플 팀 등으로 분류하는 연구 지도.
   - 선정 이유: 후속 인용 후보를 연구 가지별로 나눌 기준을 제공한다.

2. **How does Endpoint Detection use the MITRE ATT&CK Framework?**
   - 역할: 실제 EDR 규칙을 비교해 ATT&CK coverage의 한계를 검토하는 실증 연구.
   - 선정 이유: 자동 매핑이나 coverage 점수만으로 실제 방어 성능을 단정하지 않게 하는 평가 기준을 제공한다.

3. **Rule-ATT&CK Mapper (RAM): Mapping SIEM Rules to TTPs Using LLMs**
   - 역할: 구조화된 SIEM 규칙을 ATT&CK technique로 연결하는 LLM 기반 방법.
   - 선정 이유: AI×보안 자동 매핑 방법을 대표하며, 2번의 실증 평가 관점과 함께 검토할 수 있다.

4. **MITRE ATT&CK Applications in Cybersecurity and The Way Forward**
   - 역할: 대규모 문헌을 검토하고 backward/forward snowballing 절차를 제시하는 survey.
   - 선정 이유: 참고문헌을 반복적으로 거슬러 올라가는 이번 연구 목적과 직접 맞는다.

5. **MITRE ATT&CK: State of the Art and Way Forward**
   - 역할: 더 이른 시점의 ATT&CK 연구 분류체계.
   - 선정 이유: 다른 survey와 함께 비교해 공통으로 인용되는 더 이른 연구를 찾는 기준이 된다.

세 survey는 서로 독립적인 실증 증거로 중복 계산하지 않는다. 이 조합은 `분야 지도 → LLM 기반 자동 매핑 → 실제 탐지·coverage 평가`라는 보완 관계를 만든다.

## 1차 루트 그래프 관찰

- 입력: 출발 논문 5편
- 깊이: 2
- 노드 상한: 100
- 참고문헌 상한: 논문당 100
- 결과: 루트 후보 95편
- 참고문헌 DB 조회 실패: 0건

후보 수가 100-node 상한에 가까워, 이 결과는 완전탐색이나 최초 원천의 증거가 아니다. 그래프 연결은 데이터베이스 참고문헌 관계이며, 개별 원문 PDF에서 인용 문맥을 확인한 상태가 아니다.

### 우선 검토 대상 5개

아래 다섯 항목은 출발 논문 5편 중 3편에서 도달했고, 직접 인용된 출발 논문 수도 상대적으로 높아 다음 원문 검토 우선순위로 삼았다. 최종 선정·원천 확정이 아니다.

- **MITRE ATT&CK-driven Cyber Risk Assessment** — 3/5 도달, 직접 인용 출발 논문 3편. 위험평가 가지.
- **Learning the Associations of MITRE ATT&CK Adversarial Techniques** — 3/5 도달, 직접 인용 2편. technique 관계 학습 가지.
- **Linking CVE’s to MITRE ATT&CK Techniques** — 3/5 도달, 직접 인용 2편. CVE→ATT&CK 데이터 매핑 가지.
- **Automated Retrieval of ATT&CK Tactics and Techniques for Cyber Threat Reports** — 3/5 도달, 직접 인용 2편. CTI 보고서→TTP 추출 가지.
- **Assessing MITRE ATT&CK Risk Using a Cyber-Security Culture Framework** — 3/5 도달, 직접 인용 2편. 위험평가 확장 가지.

## 2차 확장과 잡음 처리

1차의 상위 후보를 다시 시작점으로 최대 2단계 확장했다. 이 과정에서 공식 ATT&CK Navigator와 `attack.mitre.org`처럼 논문이 아닌 공식 자료형 인용이 나타났다. 이들은 논문과 구분해 공식 프레임워크·기술 문서 후보로 다룬다.

반대로 Shannon의 통신 이론 등 일반 이론이나 주제와 직접 관계없는 항목도 인용 그래프에는 등장했다. 인용 연결만으로 ATT&CK 연구의 기원이라고 부르지 않고, 연구 질문과의 직접 근거가 없으면 제외 또는 보류했다.

- 2차 결과: 후보 95개, 조회 실패 2건, 시작 후보 완전 해석 5/7.
- 판정: **탐색 미완료**. 0건 실패가 완전성의 증거가 아니며, 2건 실패와 상한 도달 가능성을 보존한다.

## 다음 단계

1. 우선 검토 대상 5개와 나머지 직접 관련 후보의 공개 PDF·공식 기록을 확인한다.
2. 데이터베이스 인용 edge와 PDF 본문 인용 문맥을 구분해 기록한다.
3. `CVE→ATT&CK`, `CTI/TTP 추출`, `위험평가`, `coverage 평가`, `MITRE 공식 프레임워크` 가지별로 frontier를 보존하며 추가 추적한다.
4. 공식 MITRE 문서의 정확한 판본·버전·날짜를 확인한다.

현재 그래프 도구는 단일 호출의 노드 상한과 DB edge 중심 기록을 제공한다. 여러 호출의 방문 노드·순환·frontier를 병합해 이어가는 continuation 기능은 구현 필요로 남아 있다.

## 실행 경계

- PaperQA 외부 모델·임베딩 호출: **미실행**
- 논문 코드·설치 스크립트 실행: **미실행**
- 공개 PDF 보존 및 SHA-256 기록: 실행됨(로컬 연구 데이터에만 보존)
- 상세 로컬 분석: `${RESEARCH_DATA}/cybersecurity/mitre_attack_report_20260914T122700Z/`
