---
name: korean-paper-analysis
description: "Use when analyzing PDFs into Korean research reports."
version: 0.1.0
author: Sonamoo0407, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [papers, pdf, research, korean, reproducibility]
    related_skills: [pdf]
---

# Korean Paper Analysis Skill

Analyze every new PDF in `/home/sonamoo0407/research/inbox` into an evidence-bounded Korean Markdown report. Do not move, rename, modify, or delete source PDFs. This is a manual-on-demand workflow: it does not create a cron job, watcher, or other automation registration.

## When to Use

- The user asks to analyze papers placed in the research inbox.
- The user asks to process one named PDF from that inbox.
- Do not use for articles outside the inbox unless the user explicitly requests it.

## Prerequisites

- Root directory: `/home/sonamoo0407/research`
- Source PDFs: `inbox/`
- Reports: `reports/`
- Deduplication ledger: `state/processed.jsonl`
- Failure records: `failed/`
- Use the `pdf` skill's inspection and extraction procedure. For an image-only or substantially scanned PDF, load its OCR reference before reporting.

## Procedure

1. Discover only regular `*.pdf` files in `inbox/` with `search_files`, and compute each candidate's SHA-256 using `terminal`. Read `state/processed.jsonl` if it exists. A hash with status `success` must be skipped; do not rely on filenames for deduplication.
2. For each unprocessed hash, inspect PDF metadata and extract text per page using the `pdf` skill tooling. Detect encryption and image-only pages before analysis. If extraction is not possible, write a UTF-8 failure JSON file under `failed/` named `<sha256>.json`, containing `sha256`, `source_file`, `timestamp_utc`, `stage`, and an exact failure reason. Append a `failed` record to `state/processed.jsonl`. Do not create a report.
3. Ground all claims in the extracted PDF text, tables, figures, visible metadata, or clearly identified bibliographic information in the PDF. Never invent missing metadata, methods, results, citations, datasets, or limitations. Write `확인 불가` where the paper does not establish the requested fact. Quote text only when the wording is present in the source. Put a page number on a quotation only when the page can be verified from per-page extraction; otherwise omit the quotation rather than guessing a page.
4. Derive a conservative filename: `<year>_<first-author>_<short-title>.md`. Use a four-digit publication year and a first-author surname only if explicit; otherwise use `unknown` for that component. Use an ASCII lowercase short title of 2–6 meaningful words joined by hyphens; strip filesystem-unsafe characters. If the resulting name collides with a different hash, append the first 8 SHA-256 characters before `.md`.
5. Write the report in Korean using exactly the following numbered H2 sections, in this order. Include uncertainty explicitly rather than filling gaps.

## 1. 논문 제목, 저자, 연도, 학회 또는 저널
## 2. 한 문장 핵심 요약
## 3. 연구 질문과 연구 목적
## 4. 기존 연구와의 차별점
## 5. 연구 방법론
## 6. 사용한 데이터와 실험 설계
## 7. 주요 결과
## 8. 저자가 주장하는 기여점
## 9. 한계와 잠재적 오류
## 10. 재현 가능성 평가
## 11. 비판적 검토
## 12. 후속 연구 아이디어 3개
## 13. 내 연구에 활용할 만한 포인트
## 14. 주요 용어 설명
## 15. 참고문헌용 BibTeX 초안

For sections 9, 10, 11, 12, and 13, separate source-supported facts from analytical assessment. Assessments must be framed as conditional (for example, `본문에서 확인된 범위에서는 ...`) and must not assert unstated facts. Section 12 always contains exactly three ideas; if the evidence is insufficient, make each item a clearly labelled general follow-up direction rather than an invented finding. BibTeX is a draft: retain only fields confirmed by the paper and omit unknown fields; use `@misc` if publication venue/type cannot be verified.

6. Before recording success, re-read the report and verify: all 15 headings are present exactly once and in order; the report is non-empty; the source PDF remains at its original path; the report contains no unsupported placeholder citations or guessed page references. Then append one JSON line to `state/processed.jsonl` with `sha256`, `source_file`, `report_file`, `status: "success"`, and `processed_at_utc`. Do not append success first.

## Pitfalls

- A filename change does not make a PDF new; SHA-256 is the identity.
- Do not treat PDF metadata as authoritative when it conflicts with the paper's title page; note the conflict.
- OCR text can be erroneous. Mark low-confidence extraction as uncertain and do not infer precise numerical results from garbled text.
- Never overwrite a report belonging to another hash.
- Do not register cron, filesystem watchers, system services, or scheduled jobs unless the user separately asks.

## Verification

- Confirm all four directories exist before each run.
- Confirm every new success has exactly one success ledger entry and a readable Markdown report.
- Confirm every failed extraction has a failure JSON record and no success record for that attempt.
- Report the number of scanned, skipped, succeeded, and failed PDFs after each invocation.
