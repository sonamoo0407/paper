# 랜섬웨어 논문 선정 및 원천 추적 보고

## 1. EDS 100건 중 상위 30건 선정

2026-09-30 경기대 EDS 수집분. 제목·DOI로 중복을 확인한 뒤 게재처 우선순위와 BM25 키워드 관련도를 적용했다. 아래는 **다운로드 후보 선정** 근거다. 전문의 방법·데이터·품질을 비교해 최종 채택했다는 뜻은 아니다.

| 순위 | ID | 제목 | 게재처 분류 점수 | BM25 | 선정 점수 |
|---:|---|---|---:|---:|---:|
| 1 | KGL-093 | System-Wide Ransomware Attack Detection via Perturbation-Resilient Representation Learning | top-security-venue (125) | 87.68 | 155.69 |
| 2 | KGL-095 | Artificial Intelligence-Powered Crypto Ransomware Detection | strong-security-journal (70) | 100.0 | 105.0 |
| 3 | KGL-092 | Deep MCRan: Hybrid Analysis-Based Ransomware Detection Using Multi-Channel Data Fusion | strong-security-journal (70) | 96.03 | 103.61 |
| 4 | KGL-017 | Behavioural Detection of Ransomware and a Comprehensive Approach to Ransomware Prevention | strong-security-journal (70) | 88.79 | 101.08 |
| 5 | KGL-069 | A Comprehensive Analysis of Machine Learning-Based File Trap Selection Methods to Detect Crypto Ransomware | top-security-venue (100) | 2.15 | 100.75 |
| 6 | KGL-048 | Ransomware Detection through Temporal Correlation between Encryption and I/O Behavior | reputable-publisher-or-journal (50) | 92.36 | 82.33 |
| 7 | KGL-094 | TDMRans: Toward a Two-Stage Detection Method of Ransomware Encryption Behavior in Storage System | reputable-publisher-or-journal (50) | 87.68 | 80.69 |
| 8 | KGL-091 | Detection of Ransomware Attack in IoT-Based Smart Meter Using Hybrid Deep Learning Model | reputable-publisher-or-journal (50) | 84.02 | 79.41 |
| 9 | KGL-011 | Comparative Analysis of Machine Learning-Based Intelligent Threat Detection Systems for Ransomware Detection | reputable-publisher-or-journal (38) | 99.3 | 72.75 |
| 10 | KGL-051 | Privacy-Aware Machine Unlearning with SISA for Reinforcement Learning–Based Ransomware Detection | reputable-publisher-or-journal (38) | 94.16 | 70.96 |
| 11 | KGL-032 | Ransomware Threats and Machine Learning-based Detection: A Review | reputable-publisher-or-journal (38) | 88.64 | 69.02 |
| 12 | KGL-078 | AI-Augmented Ransomware Detection with Real-Time Threat Intelligence Using AI Models | reputable-publisher-or-journal (38) | 88.64 | 69.02 |
| 13 | KGL-086 | Ransomware Detection with ML and Deep Learning: An Evidence-Based Survey and Drift-Aware Taxonomy | reputable-publisher-or-journal (38) | 88.0 | 68.8 |
| 14 | KGL-059 | Hybrid Deep Learning Framework for Efficient Ransomware Detection | reputable-publisher-or-journal (38) | 86.73 | 68.36 |
| 15 | KGL-070 | AI-Driven Ransomware Detection and Analysis with Automated Reverse Engineering and Rollback | reputable-publisher-or-journal (38) | 86.73 | 68.36 |
| 16 | KGL-079 | Optimized AI Models for Multi-Class Malware Detection: Balancing Datasets with O-SMOTE and Detecting Ransomware with 1D-CNN | reputable-publisher-or-journal (38) | 86.73 | 68.36 |
| 17 | KGL-007 | Investigating Intra-class Imbalance In Datasets for Dynamic Ransomware Detection | reputable-publisher-or-journal (38) | 86.42 | 68.25 |
| 18 | KGL-035 | Real-Time Detection of Obfuscated Ransomware Using Optimized Machine Learning for Critical Systems | reputable-publisher-or-journal (38) | 86.12 | 68.14 |
| 19 | KGL-036 | Early Detection and Active Defense Method for Ransomware in Smart Grids | reputable-publisher-or-journal (38) | 86.12 | 68.14 |
| 20 | KGL-064 | Ransomware Detection for Linux based System Using Machine Learning | reputable-publisher-or-journal (38) | 86.12 | 68.14 |
| 21 | KGL-015 | A Federated Learning Approach Towards Cross-Architecture Ransomware Detection Using Low-Level Hardware Information | reputable-publisher-or-journal (38) | 85.51 | 67.93 |
| 22 | KGL-023 | HATE: An Explainable Hybrid Attention–Temporal Ensemble Framework for Early-Stage Ransomware Detection Using Kernel-Level File I/O Behaviour | reputable-publisher-or-journal (38) | 85.51 | 67.93 |
| 23 | KGL-044 | Entropy-Based Ransomware Detection Using File System Filters | reputable-publisher-or-journal (38) | 85.51 | 67.93 |
| 24 | KGL-084 | DB Sherlock: Dynamic Ransomware Threat Detection in MySQL Using Behavioral Profiling and Query Analytics | reputable-publisher-or-journal (38) | 85.51 | 67.93 |
| 25 | KGL-003 | Behavioral Memory-Artifact Deep Learning for Ransomware Detection with Confidence-Aware Automated Response | reputable-publisher-or-journal (38) | 85.21 | 67.82 |
| 26 | KGL-083 | A Study of Ransomware Detection and Encryption Blocking Performance Verification: Focusing on Global Antivirus | reputable-publisher-or-journal (38) | 84.91 | 67.72 |
| 27 | KGL-008 | Ard-Ppo: an Advanced Ransomware Detection Based on Proximal Policy Optimization Model | reputable-publisher-or-journal (38) | 84.61 | 67.61 |
| 28 | KGL-029 | A Comparative Study of Supervised Machine Learning Algorithms for Ransomware Detection | reputable-publisher-or-journal (38) | 84.31 | 67.51 |
| 29 | KGL-062 | A Comprehensive Review of Deep Learning Architectures for Ransomware Detection | reputable-publisher-or-journal (38) | 84.31 | 67.51 |
| 30 | KGL-005 | WannaCry Ransomware Analysis Using Reverse Engineering and Signature-Based Detection | reputable-publisher-or-journal (38) | 84.02 | 67.41 |

상위 30건 밖의 70건은 해당 선별 단계에서 미선정. 개별 원문 평가나 학술적 제외 판정은 기록되지 않았다.

## 2. citracer에 사용한 출발 논문과 선정 근거

**별도 자료:** 현재 화면의 10개 노드·14개 인용선은 9월 28일 이관 백업에서 가져왔다. 위 EDS 100건에서 이 출발 논문들을 뽑았다는 연결 장부는 확인되지 않았다.

9월 23일 공개 검색에서 Crossref 고유 147건을 확보하고 주제에 맞는 25편을 검토 장부에 올렸다. 아래 5편은 당시 핵심 검토 후보(proposed)로 보고됐다.

| ID | 출발 논문 | 연도 | 기존 상태 | 구체적 선정 이유 |
|---|---|---:|---|---|
| R1-01 | UNVEIL: A Large-Scale, Automated Approach to Detecting Ransomware | 2016 | 후보 | 탐지 · 인공 사용자 환경에서 랜섬웨어가 사용자 데이터와 상호작용하는 방식을 동적으로 분석한다. |
| R1-02 | The Aftermath of a Crypto-Ransomware Attack at a Large Academic Institution | 2018 | 후보 | 피해·복구 · 실제 대학 랜섬웨어 사고의 기술적 비용, 생산성 손실, 사회적 비용을 분석한다. |
| R1-03 | Detecting Ransomware Despite I/O Overhead: A Practical Multi-Staged Approach | 2025 | 후보 | 탐지 · I/O 모니터링의 비용 문제를 다단계 탐지 방식으로 다룬다. |
| R1-04 | Ransom Access Memories: Achieving Practical Ransomware Protection in Cloud with DeftPunk | 2024 | 후보 | 탐지·복구 · 클라우드 블록 스토리지에서 탐지와 스냅샷 기반 데이터 손실 완화를 결합한다. |
| R1-05 | The Ransomware Decade: The Creation of a Fine-Grained Dataset and a Longitudinal Study | 2025 | 후보 | 공격 흐름·데이터셋 · 장기간 랜섬웨어 공격 환경을 세분화한 데이터셋으로 연구한다. |

R1-04와 R1-05는 당시 보고의 제목 표기와 차이가 있어 그래프와 일치하는 공식 게재 제목을 사용했다. [R1-04 USENIX OSDI](https://www.usenix.org/conference/osdi24/presentation/wang-zhongyu), [R1-05 USENIX Security](https://www.usenix.org/conference/usenixsecurity25/presentation/sarabi)

## 3. 중간 논문 후보와 근거

| 순위 | 후보 | 매개중심성 | 근거 수준 |
|---:|---|---:|---|
| 1 | ShieldFS: a self-healing, ransomware-aware filesystem | 0.03241 | 구조상 매개 후보 |
| 2 | Redemption: Real-Time Protection Against Ransomware at End-Hosts | 0.02546 | 구조상 매개 후보 |
| 3 | PayBreak: Defense Against Cryptographic Ransomware | 0.01157 | 구조상 매개 후보 |

**대표 경로:** R1-03 → ShieldFS(R2-01) → Cryptovirology(R3-04).

- R1-03 → R2-01: 기존 원장 표기 `ledger/round2_trace.tsv: R1-03 PDF 14`.
- R2-01 → R3-04: 기존 원장 표기 `ledger/round3_trace.tsv: R2-01 PDF 11`.

이번 계산은 기존 원장에 원문 확인으로 기록된 간선만 사용했다. 원문 인용 문장을 재검증하지 않았으므로, ShieldFS가 실제로 어떤 방법을 전달했는지는 미확인이다.

## 4. 분석 파일과 후속 확인

- [원본 인용망 JSON](../vm-migration-backup-20260928/graph-renderer/graphs/graph-output/graph.json)
- [citracer 인터랙티브 그래프](ransomware-citracer.html) · [렌더링 코드](../scripts/render_ransomware_citracer.py)
- [중간 논문 후보 순위 HTML](ransomware-bridge-ranking.html)
- [NetMiner 입력 CSV와 점수 계산](../examples/ransomware-netminer/README.md)
- [EDS 선별 코드](../tools/kyonggi-library-collector/local_research_pipeline.py)
- [본문 인용 문맥 채점 규칙](../skills/root-paper-research/CITATION_CONTEXT_RULES.md)

citracer와 SciPy는 [피싱 실험의 설치 단계](../examples/citracer-phishing/README.md#재현)와 같은 버전을 사용한다. 저장소 루트에서 `python scripts/render_ransomware_citracer.py`로 보존 인용망의 HTML을 다시 만들 수 있다.

9월 30일의 별도 Crossref 드라이런에서는 논문 3개와 간선 2개를 확보했다. 그 연결에는 경로 중간에 오는 노드가 없어 매개중심성이 모두 0이었다. 위 순위는 9월 28일 이관본에서 계산했다.

ShieldFS의 중간 논문 역할을 확정하려면 대표 경로의 두 인용 문장을 쪽수와 함께 검토하고, 어떤 개념이나 방법이 이어졌는지 설명해야 한다.
