# 경기대 도서관 논문 수집기

경기대학교 도서관 또는 경기대 `libproxy`를 통해 브라우저 세션에서 검색 결과의 서지 메타데이터와 접근 상태를 수집하는 로컬 도구다. Discord를 검색 중계로 쓰지 않으며, 결과 장부를 파일로 바로 만든다.

## 기본 동작: 브라우저 없이 경기대 EDS 검색

기본 `direct` 모드는 경기대 도서관의 공개 EDS(Article) 검색 결과 엔드포인트를 직접 호출한다. 즉 **Chrome·로그인·비밀번호 입력 없이** 키워드별 최대 100편의 공개 서지 메타데이터와 `기관 로그인이 필요한 원문 링크` 표시를 장부로 만든다. 이는 원문 파일을 내려받지 않는다.

기관 구독 전문을 실제로 열어야 하는 경우에만 `--mode browser`와 `--auto-login`을 쓴다. 이 모드는 별도이며, 자격증명은 로컬 실행 메모리에서만 사용한다.

## 보안·이용 경계

- 기본 모드는 프로그램이 연 Chrome 창에서 사용자가 직접 로그인한다. 선택 모드 `--auto-login`은 실행 중 로컬 터미널에서만 ID·비밀번호를 묻고 라이브 로그인 화면에 입력한다. 자격증명은 파일·로그·명령줄 인자·결과물에 저장하지 않는다.
- 로그인 쿠키/브라우저 프로필은 사용자 로컬 앱 데이터 폴더에만 남으며 `outputs` 또는 Git 대상에 기록하지 않는다.
- 수집물은 제목·저자·연도·DOI·원문 링크·검색 DB·확인 시각·화면상 접근 상태다. 원본 HTML·PDF·쿠키·스크린샷은 저장하지 않는다.
- 개별 DB의 이용약관과 저작권 범위를 따라야 한다. 대량 PDF 다운로드나 우회 접근 기능은 제공하지 않는다. 전문이 필요한 항목은 `access_status`만 기록하고, 실제 열람/다운로드는 사용자가 해당 DB 화면에서 직접 결정한다.

## 설치

Windows PowerShell에서 이 폴더로 이동한 뒤 한 번만 실행한다.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 사용법

가장 쉬운 방법은 `run_collector.bat`를 더블클릭하는 것이다. Windows CMD 인코딩 문제를 피하기 위해 이 실행 파일의 화면 문구는 영어로 되어 있다. 검색어를 묻고, 완료·실패 메시지를 보여준 채 창을 유지한다.

`경기대_논문수집기_실행.bat`는 별도의 기관 로그인 수집 실행 파일이다. 이 파일은 브라우저 보조 모드를 열고 로컬 CMD 창에서만 자격증명을 받으므로, 같은 PC에 Chrome 또는 Chromium이 설치되어 있어야 한다.

```powershell
# 기본: 브라우저/로그인 없이 경기대 EDS 메타데이터 검색
python kyonggi_collector.py collect --query "ransomware detection" --max-records 100 --max-pages 10

# 선택: 기관 구독 전문의 접근 상태를 브라우저에서 확인할 때만 사용
python kyonggi_collector.py collect --mode browser --auto-login --query "ransomware detection" --max-records 100 --max-pages 10
```

실행하면 Chrome이 열린다.

1. 기본 모드에서는 바로 경기대 EDS 공개 검색 결과를 페이지 단위로 읽는다.
2. `browser` 모드에서만 경기대 도서관/프록시 DB에 로그인하고, 원하는 DB의 **결과 목록 화면**까지 이동한다.
3. browser 모드에서는 PowerShell로 돌아와 Enter를 누른다. 프로그램이 현재 결과 페이지에서 제목·링크·표시 메타데이터·접근 라벨만 읽는다.

결과는 `outputs/<UTC시각>_<검색어>/`에 생성된다.

- `records.jsonl`: 후보별 메타데이터·출처·접근 상태
- `records.csv`: 표 형태 장부
- `manifest.json`: 검색 조건·수집 수·제외/중복 수

기관 DB의 UI는 바뀔 수 있으므로, 수집 후 `records.csv`에서 제목과 출처를 반드시 빠르게 검토한다. 제목을 가져오지 못한 페이지는 원본 HTML을 저장하지 않고 `manifest.json`의 `warnings`에 남긴다.

## 공개 PDF만 내려받기

수집 결과에 들어 있는 원문 링크 중, 로그인 없이 응답 자체가 PDF인 항목만 별도 폴더에 저장할 수 있다. 로그인·쿠키·기관 구독 다운로드·CAPTCHA·유료 접근 우회는 하지 않는다.

```powershell
python kyonggi_collector.py download-public `
  --records ".\outputs\<수집폴더>\records.jsonl" `
  --output-dir ".\outputs\<수집폴더>\public-downloads" `
  --max-attempts 100 --max-downloads 100 --delay-seconds 1
```

성공한 PDF만 `public-downloads\public_pdfs`에 남고, 나머지는 `download_ledger.jsonl`에 `skipped_not_direct_pdf`, `skipped_no_public_link`, `file_too_large` 등으로 기록된다.

외부 제공처가 오래 응답하지 않으면 링크별 제한 시간 후 `timed_out`으로 보류하고 다음 항목으로 넘어간다. 중단 후 이어서 할 때는 `--start-index 57`처럼 이미 확인한 레코드 수를 넣는다.

## 기관 로그인 뒤 연결 페이지에서 받기

위의 공개 PDF 검사는 **링크 자체가 즉시 PDF를 주는지**만 확인한다. EDS의 `기관 원문 링크`를 열었을 때 로그인 뒤에 `PDF 다운로드` 버튼이 보이는 자료는 아래의 보조 검토 모드를 쓴다. Chrome에서 사용자가 직접 로그인하고, 각 제공처 페이지에서 실제 다운로드 여부를 결정한다. 도구는 다음 논문 페이지로 넘기고 저장된 PDF와 장부만 관리한다. 제공처의 다운로드 버튼을 자동으로 누르거나 로그인·CAPTCHA·구독 제한을 우회하지 않는다.

```powershell
python kyonggi_collector.py review-downloads `
  --records ".\outputs\<수집폴더>\records.jsonl" `
  --output-dir ".\outputs\<수집폴더>\institution-downloads" `
  --max-records 100
```

다운로드한 파일은 `institution-downloads\institution_downloads`에, 항목별 결과는 `institution_download_ledger.jsonl`에 남는다. 페이지를 열어 둔 상태에서 다운로드한 뒤 터미널에서 Enter를 누르면 파일을 확인하고 다음 항목으로 이동한다. `s`는 건너뛰기, `q`는 중단이다.

로그인 뒤 보이는 PDF/다운로드 버튼까지 자동으로 시도하려면 아래 모드를 쓴다. 각 링크에서 **보이는 PDF 또는 다운로드 제어 하나만** 누르고, 파일이 저장되지 않으면 장부에 남긴 뒤 다음 링크로 넘어간다. 제공처별 화면이 달라 100% 성공을 보장하지는 않지만, HTML·로그인·구매 버튼은 제외한다. 로그인·2차 인증·CAPTCHA는 사용자가 Chrome에서 직접 완료해야 한다. 기본값은 `top-tier` 우선순위라 보안 최상위 학회·저널 → 검증된 보안 저널 → IEEE/ACM·일반 학술 출처 → 나머지 순서로 먼저 시도한다.

```powershell
python kyonggi_collector.py auto-downloads `
  --records ".\outputs\<수집폴더>\records.jsonl" `
  --output-dir ".\outputs\<수집폴더>\institution-auto-downloads" `
  --max-records 100
```

결과 PDF는 `institution-auto-downloads\institution_downloads`, 성공·실패 사유는 `institution_auto_download_ledger.jsonl`에 저장된다. 실행 중에는 Chrome 창을 닫지 말고, 문제가 있는 제공처는 프로그램을 `Ctrl+C`로 멈춘 뒤 `--start-index`로 이어서 실행한다.

정렬 결과와 근거는 실행 전에 `priority_selection.csv`와 `priority_selection.jsonl`로 저장된다. 이는 EDS 메타데이터 기반의 투명한 휴리스틱이며, 공식 JCR·Scopus·SJR 사분위 등급이라고 주장하지 않는다. 정렬하지 않고 EDS 원래 순서대로 하려면 명령 끝에 `--priority source-order`를 더한다.

## 토큰 없는 로컬 분석 전처리

`local_research_pipeline.py`는 LLM을 호출하지 않고 다음을 처리한다.

1. DOI/정규화 제목 중복 제거, 탑티어·키워드(BM25) 점수화, 상위 후보 선별
2. 내려받은 PDF의 텍스트·페이지 수·SHA-256·참고문헌 DOI·초록/방법 섹션 추출
3. 선택 후보 내부의 참고문헌 DOI/정규화 제목 근거로 인용 그래프 JSON/HTML 생성

```powershell
# 100개 전체를 먼저 정렬하고 상위 30개만 로컬 선별
python local_research_pipeline.py prepare `
  --records ".\outputs\<수집폴더>\records.jsonl" `
  --query "ransomware detection" `
  --output-dir ".\outputs\<수집폴더>\local-prep" `
  --select-count 30

# 자동 다운로드된 PDF의 원문 텍스트·참고문헌을 로컬 추출
python local_research_pipeline.py extract `
  --selected-records ".\outputs\<수집폴더>\local-prep\selected_candidates.jsonl" `
  --pdf-dir ".\outputs\<수집폴더>\institution-auto-downloads\institution_downloads" `
  --output-dir ".\outputs\<수집폴더>\local-extraction"

# 원문 근거가 있는 후보 간 인용 엣지만 그래프로 만듦
python local_research_pipeline.py graph `
  --selected-records ".\outputs\<수집폴더>\local-prep\selected_candidates.jsonl" `
  --extraction ".\outputs\<수집폴더>\local-extraction\pdf_extraction.jsonl" `
  --output-dir ".\outputs\<수집폴더>\local-graph"
```

이 결과를 Hermes에 넘길 때는 `selected_candidates.jsonl`, `pdf_extraction.jsonl`, `citation_graph.json`과 실제 PDF만 전달하면 된다. LLM은 그 이후의 연구적 해석·비교·최종 채택 근거 작성에만 사용한다.

현재 수집한 ransomware 100건을 편하게 처리하려면 `run_auto_downloads.bat`를 더블클릭한다. `How many records should be processed?`에서 이번에 받을 개수만 입력한다. 예를 들어 `10`을 입력하면 첫 10개만, `30`을 입력하면 첫 30개만 처리한다.

`--auto-login`이 로그인 폼을 찾지 못하면, 해당 DB의 로그인 주소·CSS 선택자를 지정할 수 있다. 비밀번호는 절대로 인자로 넣지 않는다.

```powershell
python kyonggi_collector.py collect --mode browser --auto-login --query "ransomware detection" `
  --login-url "https://..." --username-selector "input[name='userId']" `
  --password-selector "input[type='password']" --submit-selector "button[type='submit']"
```

CAPTCHA·2차 인증·추가 약관 동의는 자동으로 우회하지 않으며, 해당 화면에서 사용자가 직접 완료해야 한다.

## Ubuntu에서 기관 로그인 다운로드 실행

Ubuntu에 Python 의존성과 Chrome/Chromium이 설치된 뒤, **사용자가 볼 수 있는 Ubuntu 터미널**에서 다음을 실행한다.

```bash
chmod +x run_institution_downloads_linux.sh
./run_institution_downloads_linux.sh "ransomware detection" 20
```

이 실행 파일은 브라우저 보조 수집(최대 지정 건수) 후, 같은 장부를 탑티어 휴리스틱으로 정렬해 `auto-downloads`를 실행한다. 계정 소유자가 해당 Ubuntu 터미널과 브라우저에서 직접 로그인해야 하며, ID·비밀번호는 명령어·결과 파일에 기록되지 않는다.

## Hermes 연결 방식

수집이 끝나면 `records.jsonl`만 VMware 공유 폴더 또는 Hermes의 새 실행 폴더로 복사한다. Hermes는 그 장부에서 R1 선정·R2 인용 추적·그래프 생성만 담당한다. 인증정보나 브라우저 프로필은 전달하지 않는다.
