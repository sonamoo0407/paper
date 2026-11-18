# NetMiner 스터디와 논문 인용 분석 적용 설계

작성일 2026-11-06. 공개 공식 자료와 현재 로컬 코드를 비교한 스터디 노트다. 아래 적용 설계는 우리 프로젝트를 위한 제안이다. NetMiner 제품을 직접 실행해 비교 검증한 결과는 아직 없다.

## 1. 공부할 질문

어떤 논문이 기반이 되었고, 후속 연구가 무엇을 발전시켰으며, 서로 다른 연구 흐름을 어떤 논문이 연결했는가? 이를 그래프 구조와 본문 인용 근거로 설명한다.

공식 NetMiner는 연결·응집·중심·역할 구조를 분석 관점으로 제시한다. 우리 프로젝트에서는 각각 인용 경로, 연구 집단, 중심성 지표, 논문 역할에 대응시켜 공부한다. [NetMiner Methodology](https://www.netminer.com/kr/netminer/methodology.php)

## 2. 공식 자료를 읽는 순서

| 순서 | 자료 | 확인할 내용 | 우리 실습 결과 |
|---|---|---|---|
| 1 | [논문 1,000편의 핵심 연구자 분석](https://netminer.com/kr/support/blog.php?bgu=view&idx=370) | 서지 수집, 저자 분석, 시각화, 해석의 연결 | 논문·저자·기관 데이터의 별도 표 |
| 2 | [핵심 키워드와 주요 토픽](https://www.netminer.com/kr/support/blog.php?bgu=view&idx=375) | 키워드·토픽 분석과 결과 해석 | 랜섬웨어 용어 사전과 주제 후보 |
| 3 | [중심성 시각화](https://netminer.com/kr/support/add_on.php?bgu=view&idx=54) | 중심성 종류를 선택하고 노드 크기·색으로 표현 | 같은 그래프에서 크기 지표 전환 |
| 4 | [구조적 공백·중개자 분석 등 공식 업데이트](https://www.netminer.com/kr/support/news.php?bgu=view&code=news&idx=384) | Brokerage, Structural Hole, Community 기능의 범위 | 각 방법이 답하는 연구 질문 정리 |
| 5 | [텍스트 공출현과 커뮤니티 튜토리얼](https://netminer.medium.com/find-topics-in-co-occurrence-networks-3b15ed622d76) | 단어 공출현망, 매개중심성, Leiden, 해상도 | 키워드 집단과 논문 인용 집단을 구별한 결과 |
| 6 | [이원 네트워크 분석 사례](https://www.netminer.com/en/support/blog.php?bgu=view&idx=402) | 개체 속성의 유사성과 연결 구조의 차이, 투영 | 논문–키워드 망과 논문–논문 망 설계 |

일부 공식 페이지는 이번 웹 도구의 본문 추출이 비어 검색에 노출된 공식 설명으로 확인했다. 메뉴 상세, 기본값, 계산식의 일치는 매뉴얼이나 제품 실행으로 추가 확인한다. 기능 목록은 알고리즘의 세부 정의까지 보증하지 않는다.

## 3. 우선 공부할 분석 방법

### 중심성

현재 citracer는 방향 있는 인용망에 대해 그래프 내부 피인용 수, PageRank, 매개중심성을 계산한다. 세 지표를 별도로 표시한다. 그래프 내부 피인용 수와 OpenAlex 같은 외부 출처의 전체 피인용 수는 출처와 집계 범위가 다르다.

매개중심성은 방향을 따라가는 모든 최단 경로에서 해당 논문이 중간에 등장하는 비율을 합산한다. 기본 설정에서는 출발점과 도착점을 제외한다. 방향 그래프 정규화 분모는 (N-1)(N-2)다. 거리 가중치를 주면 최단 경로가 달라지므로, 인용 빈도나 의미 점수를 거리로 사용하려면 변환 규칙을 먼저 정해야 한다. [NetworkX 매개중심성](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.betweenness_centrality.html)

우리 실습에서는 ShieldFS의 원점수 2⅓, 분모 72, 정규화 값 약 0.03241, 기여 경로들을 함께 표시한다. 논문이 추가되면 원점수와 분모가 모두 바뀔 수 있으므로 순위와 상위 후보의 변화도 비교한다.

### 커뮤니티

연결이 조밀한 집단을 찾아 서로 다른 연구 흐름의 후보로 삼는다. R1·R2·R3는 탐색 단계다. 커뮤니티는 연결에서 발견한 집단이다. 집단 이름은 소속 논문의 제목·초록·본문을 검토해 붙인다.

NetMiner 공식 사례에는 Louvain 사용 사례와 Leiden 안내가 있다. 로컬에서는 설치된 라이브러리 지원을 확인하고 알고리즘, 방향성, 가중치, seed, resolution을 기록한다. Louvain에서는 해상도와 실행 순서에 따라 집단이 바뀔 수 있다. 같은 자료에 여러 seed와 해상도를 적용해 후보가 얼마나 유지되는지 확인한다. [NetMiner 사례](https://www.netminer.com/en/support/blog.php?bgu=view&idx=402), [NetworkX Louvain](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html)

### Brokerage와 구조적 공백

NetMiner는 Brokerage와 Structural Hole 기능을 공식적으로 안내한다. 우리 연구에서는 집단 간 중개 역할을 공부하는 출발점으로 삼는다. 특정 Brokerage 계산식과 역할 분류가 제품에서 어떻게 구현되는지는 상세 문서로 확인해야 한다. [공식 기능 안내](https://www.netminer.com/kr/support/news.php?bgu=view&code=news&idx=384)

구조적 공백의 보완 지표로 Constraint와 Effective Size를 공부한다. 전자는 주변 관계가 얼마나 중복된 구조에 묶이는지, 후자는 주변 관계의 중복을 제외한 유효 규모를 평가한다. 수치는 원래 인적 네트워크 맥락에서 정의되었으므로 인용망에서의 의미를 별도로 설명해야 한다. 특히 NetworkX Effective Size는 방향 그래프에서도 이웃을 구성할 때 양방향 이웃을 함께 사용한다. [Constraint](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.structuralholes.constraint.html), [Effective Size](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.structuralholes.effective_size.html)

뚜쟁이 후보 카드에는 매개중심성, 연결하는 집단, 기여 경로, 본문 근거를 함께 제시한다. 구조적 공백 지표와 집단 간 연결 수는 보조 정보로 검토한다. 최종 해석은 실제 인용 문장이 어떤 방법이나 개념의 계승을 보여주는지에 근거한다.

## 4. 논문 관계를 정의하는 실습

아래는 우리 프로젝트에 제안하는 관계 모델이다.

| 관계 | 구성 | 해석 |
|---|---|---|
| 직접 인용 | A가 B를 인용하면 A → B | 참고문헌을 따라 과거로 추적 |
| 동시인용 | C가 A와 B를 함께 인용 | 함께 기반으로 언급되는 논문 쌍 |
| 서지결합 | A와 B가 공통 참고문헌을 가짐 | 참고 기반을 공유하는 논문 쌍 |
| 키워드 공출현 | 같은 초록이나 정해진 문맥에서 두 용어가 등장 | 주제·개념의 연결 |
| 공저 관계 | 같은 논문을 쓴 저자 쌍 | 연구자 협업 구조 |

각 관계의 노드 종류, 방향, 가중치, 날짜, 원본 출처를 저장한다. 인용망 화살표는 후속 논문에서 과거 논문으로 향한다. 지식 전파를 설명할 때는 이 시간적 의미를 함께 설명한다.

공통 참고문헌 개수는 서지결합의 첫 실습으로 사용하고, 참고문헌이 많은 논문의 영향을 줄이는 정규화 방법을 비교한다. 미확보 참고문헌을 인용 없음으로 처리하지 않도록 추출 성공·미확인 상태를 저장한다.

## 5. 재현 실험 순서

1. 현재 보존 자료 10편·14개 인용선을 고정하고 입력 파일·버전·분석 조건을 기록한다.
2. 매개중심성 원점수와 정규화 값을 수작업 가능한 작은 그래프로 대조한다. 고립 노드와 동률 경로도 확인한다.
3. 피인용 수, PageRank, 매개중심성 순위를 한 표에 놓고 높은 이유의 차이를 설명한다.
4. 커뮤니티를 계산하고 여러 해상도·seed의 집단과 매개 후보 변화를 비교한다.
5. 집단 간 중개 후보를 선정하고 본문 인용 근거를 대조한다. 구조적 연결과 내용상의 계승을 각각 기록한다.
6. 확보 논문과 참고문헌을 확장하고 후보 순위의 변화, PDF 확보율, 참고문헌 추출률을 보고한다.
7. NetMiner를 사용할 수 있는 경우 동일한 입력으로 방향·가중치·정규화·자기고리 조건을 맞춰 교차 검증한다. 커뮤니티는 번호 대신 소속 논문으로 비교한다.

기반 논문은 제안 시점과 후속 연구의 계승 근거, 발전 논문은 실제 방법·실험의 변화, 매개 논문은 집단 연결과 본문상의 전달 근거로 각각 평가한다. 연도나 네트워크 점수만으로 역할을 확정하지 않는다.

## 6. 코드 적용 순서와 완료 조건

| 순서 | 수정 대상 | 완료 조건 |
|---|---|---|
| 1 | outputs/render-ransomware-citracer.py 및 HTML·보고서 | 기존 선정 이유·파일 위치와 함께 원점수·분모·기여 경로·세 지표 표시 |
| 2 | 인용망 분석 결과 | 커뮤니티 ID, 집단별 논문, 알고리즘·seed·해상도 저장 |
| 3 | 후보 상세 카드 | 연결 집단과 실제 인용 경로, 인용 근거 위치 표시 |
| 4 | 본문 분석 장부 | 인용 문장·주변 문맥·PDF 페이지·확인 상태 기록 |
| 5 | Hermes 최종 보고 | 수집 범위·선정 이유·기반/발전/매개 해석·파일 위치를 한 번에 출력 |

현재 코드는 external/citracer/citracer/analytics.py에서 중심성을 계산하고 outputs/render-ransomware-citracer.py에서 랜섬웨어 결과를 렌더링한다. 연구용 재현 실습으로 계산 조건을 검증한 뒤 화면에 반영한다.

## 7. 결과 화면의 목표

노드 색을 인용 단계와 커뮤니티 중 선택하고 크기는 피인용 수·PageRank·매개중심성 중 선택한다. 논문을 클릭하면 원래 선정 이유, 점수 계산 근거, 연결 집단, 인용 경로, 본문 근거, 분석 파일 위치를 연다. R1·R2·R3 표기는 항상 보존한다.

키워드 전처리에는 불용어, 동의어, 복합어, 문맥 단위의 정의를 기록한다. ransomware detection과 detection을 어떻게 다룰지 정하고 전처리 전후 결과를 비교한다. 논문 집단과 키워드 집단의 해석을 각각 기록한다.

수집·추출·지표·그래프 계산은 모델 호출 없는 로컬 처리로 설계한다. 원문 문맥을 해석하는 모델 호출과 Hermes 요청 처리·보고에는 토큰이 사용될 수 있다.

## 8. 확인 범위

2026-11-06 공개 공식 자료를 조사하고 기존 코드의 계산 경로를 확인했다. 이 문서는 스터디 및 적용 설계이며 새 분석 기능의 구현 완료나 NetMiner와의 수치 일치를 의미하지 않는다. 현재 10편 그래프에서 나온 집단과 순위는 해당 관측 범위의 결과다. 논문 후보 선정과 인용망 확장에 따른 표본 편향을 후속 실험에서 확인한다.
