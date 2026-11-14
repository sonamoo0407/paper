# citracer 피싱 인용 문맥 실험

citracer는 특정 개념이 언급된 문장 주변의 인용을 찾아 논문 간 연결을 만든다. 확보한 하위 논문도 같은 방식으로 분석하며, HTML 그래프와 PageRank·매개중심성을 출력한다. 경기대 EDS 수집은 기존 수집기가 담당한다.

## 2026-10-14 시험 결과

| 파서 | 분석 PDF | 키워드 문맥 | 노드 | 간선 |
| --- | ---: | ---: | ---: | ---: |
| PyMuPDF 간이 파싱 | 1 | 122 | 11 | 10 |
| 로컬 GROBID | 3 | 454 | 13 | 20 |

GROBID 결과의 간선은 개념 연관 인용 12개와 서지 기반 보조 연결 8개다. 두 종류의 연결이 중심성 계산에 들어갔으므로 그래프 범위가 달라지면 순위도 달라질 수 있다. 표에 포함한 하위 PDF 두 편은 미리 확보하고 제목으로 매칭했다. 간이 파서는 제목에 저자 문자열이 섞였고, GROBID는 리뷰 논문의 참고문헌 15개에서 17개 항목을 생성했다. 결과는 기능 검증으로 기록하며, 연구에 활용할 간선은 원문과 대조해야 한다.

## 재현

저장소 루트에서 실행한다. Python 가상환경과 Docker를 사용한다. [citracer 원본](https://github.com/marcpinet/citracer/tree/733adab034bdc0e64be63f188654704d8a21ae27)은 시험한 커밋으로 고정했다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "git+https://github.com/marcpinet/citracer.git@733adab034bdc0e64be63f188654704d8a21ae27" scipy
New-Item -ItemType Directory -Force runs/citracer-phishing | Out-Null
curl.exe -fL https://arxiv.org/pdf/2205.07411 -o runs/citracer-phishing/phishing_review_2205.07411.pdf
curl.exe -fL https://www.usenix.org/system/files/sec21-lin.pdf -o runs/citracer-phishing/phishpedia.pdf
curl.exe -fL https://www.usenix.org/system/files/sec20-oest-phishtime.pdf -o runs/citracer-phishing/phishtime.pdf
docker run -d --name paper-citracer-grobid --init --ulimit core=0 -p 127.0.0.1:18070:8070 --memory 4g --cpus 2 grobid/grobid:0.9.1-crf
```

`curl.exe -f http://127.0.0.1:18070/api/isalive`이 성공하면 실행한다.

```powershell
.\.venv\Scripts\python.exe -X utf8 examples/citracer-phishing/smoke_test_local.py --pdf runs/citracer-phishing/phishing_review_2205.07411.pdf --output-dir runs/citracer-phishing/result --keyword phishing --resolve-limit 0 --local-corpus examples/citracer-phishing/local_corpus.json
```

결과는 `runs/citracer-phishing/result`의 HTML·JSON·GraphML·CSV와 `report.json`에서 확인한다. `--resolve-limit 0` 실행은 로컬 PDF와 파서만 사용한다. 시험에 PDF를 제공하지 않은 항목도 `unavailable`로 표시된다. 실행을 마치면 `docker stop paper-citracer-grobid`로 시험용 컨테이너를 멈춘다.
