"""Manual-login Kyonggi Library metadata collector.

The program deliberately never sees credentials. It drives a dedicated Chrome
profile, waits for the user to complete login/search, then exports only visible
bibliographic metadata from result pages.
"""

from __future__ import annotations

import argparse
import base64
import csv
import getpass
import http.cookiejar
import hashlib
import json
import mimetypes
import multiprocessing as mp
import os
import queue
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen


LIBRARY_HOME = "https://library.kyonggi.ac.kr/"
EDS_SEARCH = "https://library.kyonggi.ac.kr/eds/brief/discoveryResult"
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", re.I)
ACCESS_PATTERNS = (
    ("full_text", re.compile(r"full\s*text|pdf\s*full|원문\s*(보기|제공|이용)", re.I)),
    ("institutional_access", re.compile(r"institution|login|구독|교내|인증", re.I)),
    ("metadata_only", re.compile(r"abstract|초록|메타데이터|서지", re.I)),
)


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return value[:80] or "query"


def profile_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "KyonggiLibraryCollector" / "chrome-profile"
    return Path.home() / ".kyonggi-library-collector" / "chrome-profile"


def build_driver(profile: Path, *, reuse_open: bool = False):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError as exc:
        raise SystemExit("Selenium is missing. Run: pip install -r requirements.txt") from exc

    options = Options()
    if reuse_open:
        port_file = profile / "DevToolsActivePort"
        if not port_file.is_file():
            raise SystemExit("The collector's signed-in Chrome window is not open.")
        port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
        options.debugger_address = f"127.0.0.1:{port}"
        return webdriver.Chrome(options=options)
    options.add_argument(f"--user-data-dir={profile}")
    options.add_argument("--new-window")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(options=options)


def first_visible(driver: object, selectors: list[str]):
    """Return the first displayed selector match, or None without logging DOM."""
    from selenium.webdriver.common.by import By

    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            if element.is_displayed():
                return element
    return None


def open_login_page(driver: object, library_home: str, login_url: str | None) -> None:
    """Open an explicit login URL or follow a visible login control from the library."""
    if login_url:
        driver.get(login_url)
        return
    driver.get(library_home)
    login = first_visible(
        driver,
        [
            'a[href*="login" i]', 'button[aria-label*="로그인"]',
            'a[aria-label*="로그인"]', 'button[class*="login" i]',
            'a[class*="login" i]',
        ],
    )
    if login is not None:
        driver.execute_script("arguments[0].click()", login)
        time.sleep(1)


def login_from_local_prompt(driver: object, args: argparse.Namespace) -> None:
    """Fill only a live login form. Credentials never enter CLI args, logs or files."""
    from selenium.webdriver.support.ui import WebDriverWait

    print("ID/password are used only in this running process and are never saved.")
    username = input("경기대 ID: ").strip()
    password = getpass.getpass("경기대 비밀번호 (화면에 표시되지 않음): ")
    if not username or not password:
        raise SystemExit("Both ID and password are required.")

    open_login_page(driver, args.library_home, args.login_url)
    username_selectors = ([args.username_selector] if args.username_selector else []) + [
        'input[name="userId"]', 'input[name="username"]', 'input[name="userid"]',
        'input[id*="user" i]', 'input[id*="id" i]', 'input[type="email"]',
    ]
    password_selectors = ([args.password_selector] if args.password_selector else []) + [
        'input[type="password"]',
    ]
    user_box = first_visible(driver, username_selectors)
    password_box = first_visible(driver, password_selectors)
    if user_box is None or password_box is None:
        raise SystemExit(
            "Could not find the login inputs. Check the login page or provide "
            "--login-url / --username-selector / --password-selector."
        )
    user_box.clear()
    user_box.send_keys(username)
    password_box.clear()
    password_box.send_keys(password)
    # Explicitly drop the Python reference before clicking; the browser owns the submitted value.
    password = ""
    submit_selectors = ([args.submit_selector] if args.submit_selector else []) + [
        'button[type="submit"]', 'input[type="submit"]',
        'button[class*="login" i]', 'button[aria-label*="로그인"]',
    ]
    submit = first_visible(driver, submit_selectors)
    if submit is None:
        password_box.send_keys("\n")
    else:
        driver.execute_script("arguments[0].click()", submit)
    try:
        WebDriverWait(driver, 20).until(lambda d: first_visible(d, password_selectors) is None)
    except Exception:
        print("Login page is still visible. Complete any CAPTCHA, MFA, or agreement in Chrome.")
        input("Press Enter here after login is complete: ")


def current_library_host(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == "library.kyonggi.ac.kr" or host.endswith(".kyonggi.ac.kr")


def classify_access(text: str) -> str:
    for label, pattern in ACCESS_PATTERNS:
        if pattern.search(text):
            return label
    return "unconfirmed"


def extract_visible_results(driver: object) -> list[dict[str, str]]:
    """Return only rendered result-card text; never return page HTML or cookies."""
    rows = driver.execute_script(
        """
        const cardSelectors = [
          'article', '[role="article"]', '[data-testid*="result"]',
          '[class*="search-result"]', '[class*="SearchResult"]',
          '[class*="result-item"]', '[class*="ResultItem"]',
          'li[class*="result"]', '.record'
        ];
        const cards = [...new Set(cardSelectors.flatMap(s => [...document.querySelectorAll(s)]))]
          .filter(el => el.offsetParent !== null)
          .filter(el => (el.innerText || '').trim().length >= 12)
          .slice(0, 250);
        return cards.map(card => {
          const links = [...card.querySelectorAll('a[href]')]
            .filter(a => (a.innerText || '').trim().length >= 4);
          const titleLink = links.sort((a,b) => (b.innerText || '').length - (a.innerText || '').length)[0];
          return {
            title: (titleLink?.innerText || '').replace(/\\s+/g, ' ').trim(),
            url: titleLink?.href || '',
            text: (card.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 4000)
          };
        });
        """
    )
    output: list[dict[str, str]] = []
    for row in rows:
        title = str(row.get("title") or "").strip()
        text = str(row.get("text") or "").strip()
        if not title or len(title) < 4:
            continue
        doi = DOI_PATTERN.search(text)
        output.append(
            {
                "title": title,
                "record_url": str(row.get("url") or ""),
                "doi": doi.group(0).rstrip(".,;) ") if doi else "",
                "display_metadata": text,
                "access_status": classify_access(text),
            }
        )
    return output


def fingerprint(record: dict[str, str]) -> str:
    key = record["doi"].lower() or re.sub(r"\W+", "", record["title"].lower())
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def next_page(driver: object) -> bool:
    """Click an enabled, visible next-page control when one exists."""
    buttons = driver.execute_script(
        """
        return [...document.querySelectorAll('button, a, [role="button"]')]
          .filter(el => el.offsetParent !== null)
          .map(el => ({
            text: (el.innerText || el.getAttribute('aria-label') || '').trim(),
            disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true'
          }));
        """
    )
    candidates = [item["text"] for item in buttons if not item["disabled"] and re.search(r"^(next|다음|>|›|→)", item["text"], re.I)]
    if not candidates:
        return False
    target_text = candidates[0]
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    before = driver.current_url + "\n" + driver.find_element(By.TAG_NAME, "body").text[:500]
    controls = driver.find_elements(By.CSS_SELECTOR, "button, a, [role='button']")
    for control in controls:
        label = (control.text or control.get_attribute("aria-label") or "").strip()
        if label == target_text and control.is_displayed() and control.is_enabled():
            driver.execute_script("arguments[0].click()", control)
            try:
                WebDriverWait(driver, 12).until(
                    lambda d: (d.current_url + "\n" + d.find_element(By.TAG_NAME, "body").text[:500]) != before
                )
            except Exception:
                return False
            return True
    return False


def export_records(records: list[dict[str, str]], output: Path, manifest: dict[str, object]) -> None:
    output.mkdir(parents=True, exist_ok=False)
    with (output / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    fields = [
        "candidate_id", "title", "authors", "year", "publication_source", "doi",
        "record_url", "fulltext_url", "source_host", "query", "collected_utc",
        "access_status", "display_metadata",
    ]
    with (output / "records.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def collect(args: argparse.Namespace) -> int:
    profile = profile_dir()
    profile.mkdir(parents=True, exist_ok=True)
    driver = build_driver(profile)
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    raw_rows_seen = 0
    warnings: list[str] = []
    try:
        if args.auto_login:
            login_from_local_prompt(driver, args)
        else:
            driver.get(args.library_home)
            print("Chrome opened. Log in to Kyonggi Library/libproxy and navigate to a results page.")
        input("Press Enter here when the results list is visible: ")
        if not current_library_host(driver.current_url):
            raise SystemExit("Current page is not Kyonggi Library or its kyonggi.ac.kr proxy.")
        source_host = urlparse(driver.current_url).hostname or ""
        for page in range(1, args.max_pages + 1):
            page_rows = extract_visible_results(driver)
            if not page_rows:
                warnings.append(f"page_{page}: visible result cards were not detected")
                break
            for row in page_rows:
                raw_rows_seen += 1
                key = fingerprint(row)
                if key in seen:
                    continue
                seen.add(key)
                row.update(
                    {
                        "candidate_id": f"KGL-{len(records)+1:03d}",
                        "source_host": source_host,
                        "query": args.query,
                        "collected_utc": utc_now(),
                    }
                )
                records.append(row)
                if len(records) >= args.max_records:
                    break
            print(f"Page {page} complete: {len(records)} deduplicated candidates")
            if len(records) >= args.max_records or not next_page(driver):
                break
            time.sleep(1)
        output = Path(args.output_dir) / f"{utc_now()}_{safe_name(args.query)}"
        manifest = {
            "tool": "kyonggi-library-collector",
            "query": args.query,
            "source_host": source_host,
            "collected_utc": utc_now(),
            "max_pages": args.max_pages,
            "max_records": args.max_records,
            "collected_records": len(records),
            "duplicates_removed": max(0, raw_rows_seen - len(records)),
            "warnings": warnings,
            "boundary": "Visible metadata/access labels only. No credentials, cookies, page HTML, PDFs, or downloads were stored.",
        }
        export_records(records, output, manifest)
        print(f"Complete: {len(records)} records -> {output.resolve()}")
        return 0
    finally:
        driver.quit()


def text_of(element: object) -> str:
    return " ".join(element.get_text(" ", strip=True).split()) if element else ""


def first_year(value: str) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", value)
    return match.group(0) if match else ""


def direct_eds_page(opener: object, query: str, page: int) -> list[dict[str, str]]:
    """Read Kyonggi's public EDS result page directly; no browser or credentials."""
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise SystemExit("BeautifulSoup is missing. Run: pip install -r requirements.txt") from exc
    url = f"{EDS_SEARCH}?pn={page}&st=KWRD&service_type=brief&si=&q={quote_plus(query)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; KyonggiLibraryCollector/0.1)"})
    with opener.open(request, timeout=30) as response:
        page_html = response.read()
    soup = BeautifulSoup(page_html, "html.parser")
    records: list[dict[str, str]] = []
    for item in soup.select("ul.resultList.resultDetail > li.items"):
        title_link = item.select_one("dd.title a.searchTitle")
        if not title_link:
            continue
        title = text_of(title_link)
        source = text_of(item.select_one("dd.sourceTitle"))
        authors = text_of(item.select_one("dd.info.author"))
        text = text_of(item)
        doi_match = DOI_PATTERN.search(text)
        fulltext_link = item.select_one("dd.link a[href*='outlink']")
        records.append(
            {
                "title": title,
                "authors": authors,
                "year": first_year(source),
                "publication_source": source,
                "doi": doi_match.group(0).rstrip(".,;) ") if doi_match else "",
                "record_url": urljoin(EDS_SEARCH, title_link.get("href", "")),
                "fulltext_url": urljoin(EDS_SEARCH, fulltext_link.get("href", "")) if fulltext_link else "",
                "display_metadata": text[:4000],
                "access_status": "institutional_link_requires_login" if fulltext_link else "metadata_only",
            }
        )
    return records


def collect_direct(args: argparse.Namespace) -> int:
    """Collect up to N public EDS metadata records without opening a browser."""
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    raw_rows_seen = 0
    warnings: list[str] = []
    # The public EDS endpoint issues a short-lived verification cookie. This
    # in-memory jar exists only for this run and is never written to disk.
    opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for page in range(1, args.max_pages + 1):
        try:
            page_rows = direct_eds_page(opener, args.query, page)
        except Exception as exc:
            warnings.append(f"page_{page}: {type(exc).__name__}")
            break
        if not page_rows:
            break
        for row in page_rows:
            raw_rows_seen += 1
            key = fingerprint(row)
            if key in seen:
                continue
            seen.add(key)
            row.update(
                {
                    "candidate_id": f"KGL-{len(records)+1:03d}",
                    "source_host": "library.kyonggi.ac.kr/EDS",
                    "query": args.query,
                    "collected_utc": utc_now(),
                }
            )
            records.append(row)
            if len(records) >= args.max_records:
                break
        print(f"EDS page {page} complete: {len(records)} deduplicated candidates")
        if len(records) >= args.max_records:
            break
    output = Path(args.output_dir) / f"{utc_now()}_{safe_name(args.query)}"
    manifest = {
        "tool": "kyonggi-library-collector",
        "mode": "direct-eds-metadata",
        "query": args.query,
        "source_host": "library.kyonggi.ac.kr/EDS",
        "collected_utc": utc_now(),
        "max_pages": args.max_pages,
        "max_records": args.max_records,
        "collected_records": len(records),
        "duplicates_removed": max(0, raw_rows_seen - len(records)),
        "warnings": warnings,
        "boundary": "Public EDS metadata and institutional-link labels only. No browser, credentials, cookies, page HTML, PDFs, or downloads were used or stored.",
    }
    export_records(records, output, manifest)
    print(f"Complete: {len(records)} records -> {output.resolve()}")
    return 0


def public_download_url(record: dict[str, object]) -> str:
    """Prefer the provider target behind Kyonggi's outlink, without credentials."""
    link = str(record.get("fulltext_url") or "")
    query = parse_qs(urlparse(link).query)
    return query.get("targetUrl", [link])[0]


def pdf_filename(record: dict[str, object]) -> str:
    prefix = safe_name(str(record.get("candidate_id") or "paper"))
    title = safe_name(str(record.get("title") or "untitled"))
    return f"{prefix}_{title[:100]}.pdf"


def public_pdf_worker(url: str, partial_path: str, max_bytes: int, result_queue: object) -> None:
    """One killable worker per URL so a provider cannot stall the whole run."""
    partial = Path(partial_path)
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; KyonggiLibraryCollector/0.1)"})
        with urlopen(request, timeout=8) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            disposition = (response.headers.get("Content-Disposition") or "").lower()
            result = {"final_url_host": urlparse(response.url).hostname or ""}
            if "pdf" not in content_type and ".pdf" not in disposition:
                result_queue.put({"status": "skipped_not_direct_pdf", **result})
                return
            total = 0
            with partial.open("wb") as handle:
                while chunk := response.read(1024 * 128):
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError("file_too_large")
                    handle.write(chunk)
        if partial.read_bytes()[:5] != b"%PDF-":
            partial.unlink(missing_ok=True)
            result_queue.put({"status": "skipped_non_pdf_content", **result})
            return
        result_queue.put({"status": "downloaded_public_pdf", "bytes": total, **result})
    except ValueError as exc:
        partial.unlink(missing_ok=True)
        result_queue.put({"status": str(exc)})
    except Exception as exc:
        partial.unlink(missing_ok=True)
        result_queue.put({"status": f"failed_{type(exc).__name__}"})


def download_public_pdfs(args: argparse.Namespace) -> int:
    """Save only unauthenticated, direct PDF responses; never sends login data."""
    records_path = Path(args.records)
    if not records_path.is_file():
        raise SystemExit(f"records file not found: {records_path}")
    all_records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = all_records[args.start_index :]
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    pdf_dir = target / "public_pdfs"
    pdf_dir.mkdir(exist_ok=True)
    ledger_path = target / "download_ledger.jsonl"
    context = mp.get_context("spawn")
    downloaded = 0
    attempted = 0
    max_bytes = args.max_mb * 1024 * 1024
    with ledger_path.open("w", encoding="utf-8") as ledger:
        for record in records:
            if attempted >= args.max_attempts or downloaded >= args.max_downloads:
                break
            url = public_download_url(record)
            entry = {
                "candidate_id": record.get("candidate_id"),
                "title": record.get("title"),
                "source_url_host": urlparse(url).hostname or "",
                "checked_utc": utc_now(),
            }
            if not url or not urlparse(url).scheme.startswith("http"):
                entry["status"] = "skipped_no_public_link"
                ledger.write(json.dumps(entry, ensure_ascii=False) + "\n")
                continue
            attempted += 1
            partial = pdf_dir / (pdf_filename(record) + ".part")
            final = pdf_dir / pdf_filename(record)
            try:
                result_queue = context.Queue()
                worker = context.Process(target=public_pdf_worker, args=(url, str(partial), max_bytes, result_queue))
                worker.start()
                worker.join(args.timeout_seconds)
                if worker.is_alive():
                    worker.terminate()
                    worker.join()
                    partial.unlink(missing_ok=True)
                    result = {"status": "timed_out"}
                else:
                    try:
                        result = result_queue.get(timeout=0.5)
                    except queue.Empty:
                        result = {"status": "failed_no_result"}
                result_queue.close()
                if result["status"] == "downloaded_public_pdf":
                    if final.exists():
                        final = pdf_dir / f"{final.stem}_{downloaded+1}.pdf"
                    partial.replace(final)
                    downloaded += 1
                    result["file"] = final.name
                entry.update(result)
            except Exception as exc:
                partial.unlink(missing_ok=True)
                entry["status"] = f"failed_{type(exc).__name__}"
            ledger.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(
                f"Checked {attempted}/{min(len(records), args.max_attempts)} links; public PDFs saved: {downloaded}",
                flush=True,
            )
            time.sleep(args.delay_seconds)
    manifest = {
        "tool": "kyonggi-library-collector",
        "mode": "public-pdf-only",
        "source_records": str(records_path),
        "checked_links": attempted,
        "downloaded_public_pdfs": downloaded,
        "boundary": "Only direct unauthenticated PDF responses were saved. No login, cookies, paywall bypass, CAPTCHA bypass, or institution-only download was attempted.",
    }
    (target / "download_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Complete: {downloaded} public PDFs -> {pdf_dir.resolve()}")
    return 0


def browser_assisted_downloads(args: argparse.Namespace) -> int:
    """Open each institutional link after a user signs in; the user chooses each download.

    This deliberately does not click provider download controls, solve challenges, or
    supply credentials.  It only provides the repetitive navigation, a dedicated
    download folder, and an auditable ledger of files the signed-in user saved.
    """
    records_path = Path(args.records)
    if not records_path.is_file():
        raise SystemExit(f"records file not found: {records_path}")
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = records[args.start_index : args.start_index + args.max_records]
    target = Path(args.output_dir)
    pdf_dir = target / "institution_downloads"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = target / "institution_download_ledger.jsonl"

    driver = build_driver(profile_dir())
    # Chrome owns downloads, but this run's target folder is explicit and separate
    # from the regular profile download location.
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(pdf_dir.resolve())})
    print("Chrome opened. Log in to Kyonggi Library/libproxy in this window.")
    driver.get(args.library_home)
    input("After login is complete, press Enter here. The program will then open one record at a time: ")
    saved = 0
    try:
        with ledger_path.open("w", encoding="utf-8") as ledger:
            for index, record in enumerate(records, start=args.start_index + 1):
                link = str(record.get("fulltext_url") or "")
                entry = {
                    "candidate_id": record.get("candidate_id"),
                    "title": record.get("title"),
                    "record_index": index,
                    "opened_utc": utc_now(),
                }
                if not link:
                    entry["status"] = "skipped_no_institutional_link"
                    ledger.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    continue
                before = {item.name for item in pdf_dir.glob("*.pdf")}
                driver.get(link)
                print(f"\n[{index}] {record.get('candidate_id')} — {record.get('title')}")
                choice = input("In Chrome, download only if permitted. Enter=record result, s=skip, q=stop: ").strip().lower()
                if choice == "q":
                    break
                if choice == "s":
                    entry["status"] = "skipped_by_user"
                else:
                    # Allow Chrome to finish a just-started download, without polling a provider.
                    deadline = time.time() + args.download_wait_seconds
                    while time.time() < deadline and list(pdf_dir.glob("*.crdownload")):
                        time.sleep(1)
                    added = [item for item in pdf_dir.glob("*.pdf") if item.name not in before]
                    if added:
                        entry["status"] = "downloaded_by_signed_in_user"
                        entry["files"] = [item.name for item in added]
                        entry["bytes"] = sum(item.stat().st_size for item in added)
                        saved += len(added)
                    else:
                        entry["status"] = "no_pdf_saved"
                ledger.write(json.dumps(entry, ensure_ascii=False) + "\n")
                ledger.flush()
                print(f"Recorded {index}; PDFs saved in this review: {saved}")
    finally:
        driver.quit()
    manifest = {
        "tool": "kyonggi-library-collector",
        "mode": "user-assisted-institution-download",
        "source_records": str(records_path),
        "records_opened_or_recorded": len(records),
        "pdfs_saved_by_signed_in_user": saved,
        "boundary": "The user logged in and chose each download in Chrome. The tool did not receive credentials, click provider download controls, or bypass access restrictions.",
    }
    (target / "institution_download_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Complete: {saved} user-approved PDFs -> {pdf_dir.resolve()}")
    return 0


def newly_saved_pdfs(pdf_dir: Path, before: set[str], wait_seconds: int) -> list[Path]:
    """Wait briefly for Chrome's own download to finish and return new PDFs."""
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        added = [item for item in pdf_dir.glob("*.pdf") if item.name not in before]
        if added and not list(pdf_dir.glob("*.crdownload")):
            return added
        time.sleep(1)
    return [item for item in pdf_dir.glob("*.pdf") if item.name not in before]


TOP_SECURITY_VENUES = re.compile(
    r"usenix\s+security|ieee\s+symposium\s+on\s+security|"
    r"security\s+and\s+privacy\s*\(.*oakland|acm\s+ccs|computer\s+and\s+communications\s+security|"
    r"network\s+and\s+distributed\s+system\s+security|\bndss\b|"
    r"research\s+in\s+attacks.*defenses|\braid\b|european\s+symposium\s+on\s+research.*computer\s+security|"
    r"\besorics\b|annual\s+computer\s+security\s+applications\s+conference|\bacsac\b|"
    r"acm\s+transactions\s+on\s+privacy\s+and\s+security|\btops\b|"
    r"ieee\s+transactions\s+on\s+information\s+forensics\s+and\s+security|\btifs\b|"
    r"ieee\s+transactions\s+on\s+dependable\s+and\s+secure\s+computing|\btdsc\b",
    re.I,
)
STRONG_SECURITY_JOURNALS = re.compile(
    r"computers?\s*&\s*security|journal\s+of\s+information\s+security\s+and\s+applications|"
    r"digital\s+threats:\s+research\s+and\s+practice|international\s+journal\s+of\s+information\s+security|"
    r"journal\s+of\s+computer\s+virology|forensic\s+science|cybersecurity\s+\(springer\)",
    re.I,
)


def top_tier_score(record: dict[str, object]) -> tuple[int, str, str]:
    """Return a transparent source-quality heuristic, never a claimed JCR rank."""
    source = str(record.get("publication_source") or "")
    display = str(record.get("display_metadata") or "")
    full = f"{source} {display}"
    score = 0
    reasons: list[str] = []
    if TOP_SECURITY_VENUES.search(full):
        score += 100
        reasons.append("recognized top security venue")
    elif STRONG_SECURITY_JOURNALS.search(full):
        score += 75
        reasons.append("established security journal")
    elif re.search(r"ieee\s+access|ieee\s+communications\s+standards\s+magazine", full, re.I):
        score += 45
        reasons.append("established IEEE publication")
    elif re.search(r"\bIEEE\b|\bACM\b", full, re.I):
        score += 25
        reasons.append("IEEE/ACM publication")
    if re.search(r"publication\s+type\s+academic\s+journal", display, re.I):
        score += 20
        reasons.append("peer-reviewed journal record")
    elif re.search(r"publication\s+type\s+conference", display, re.I):
        score += 8
        reasons.append("conference record")
    elif re.search(r"publication\s+type\s+ebook", display, re.I):
        score -= 30
        reasons.append("ebook, lower research priority")
    if re.search(r"ransomware.*detect|detect.*ransomware", str(record.get("title") or ""), re.I):
        score += 5
        reasons.append("direct detection relevance")
    if score >= 90:
        tier = "top-security-venue"
    elif score >= 60:
        tier = "strong-security-journal"
    elif score >= 30:
        tier = "reputable-publisher-or-journal"
    else:
        tier = "general-or-lower-evidence"
    return score, tier, "; ".join(reasons) or "metadata did not identify a recognized venue"


def prioritize_records(records: list[dict[str, object]], priority: str) -> list[dict[str, object]]:
    annotated: list[dict[str, object]] = []
    for source_position, record in enumerate(records, start=1):
        item = dict(record)
        score, tier, reason = top_tier_score(item)
        item["source_position"] = source_position
        item["priority_score"] = score
        item["priority_tier"] = tier
        item["priority_reason"] = reason
        annotated.append(item)
    if priority == "top-tier":
        annotated.sort(key=lambda item: (-int(item["priority_score"]), int(item["source_position"])))
    for rank, item in enumerate(annotated, start=1):
        item["priority_rank"] = rank
    return annotated


def export_priority_selection(records: list[dict[str, object]], target: Path, priority: str) -> None:
    """Persist the precise order and reasons used before any provider page opens."""
    with (target / "priority_selection.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    fields = [
        "priority_rank", "priority_score", "priority_tier", "priority_reason", "source_position",
        "candidate_id", "title", "authors", "year", "publication_source", "doi", "fulltext_url",
    ]
    with (target / "priority_selection.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    (target / "priority_selection_manifest.json").write_text(
        json.dumps(
            {
                "priority_mode": priority,
                "method": "transparent venue/publisher/type heuristic; this is not a JCR, Scopus, or SJR quartile claim",
                "records_ranked": len(records),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def click_visible_pdf_control(driver: object) -> dict[str, str] | None:
    """Click one likely PDF/download control on the current provider page.

    This is intentionally conservative: it ignores sign-in, account, purchase,
    and navigation controls and clicks at most one highest-scoring visible control.
    """
    from selenium.webdriver.common.by import By

    for selector in ("a.xpl-btn-pdf[href*='/stamp/']", "a[href*='/stamp/stamp.jsp']"):
        for button in driver.find_elements(By.CSS_SELECTOR, selector):
            if button.is_displayed() and button.is_enabled():
                button.click()
                return {"text": "IEEE PDF"}
    candidates: list[tuple[int, object, dict[str, str]]] = []
    for element in driver.find_elements(By.CSS_SELECTOR, "a[href], button, input[type='button'], input[type='submit']"):
        try:
            if not element.is_displayed() or not element.is_enabled():
                continue
            text = " ".join(
                filter(
                    None,
                    [
                        element.text,
                        element.get_attribute("aria-label"),
                        element.get_attribute("title"),
                        element.get_attribute("value"),
                    ],
                )
            ).lower()
            href = (element.get_attribute("href") or "").lower()
            combined = f"{text} {href}"
            if re.search(r"login|log in|sign in|로그인|account|purchase|buy|cart|구매", combined):
                continue
            score = 0
            if ".pdf" in href:
                score += 100
            if "download" in href:
                score += 60
            if re.search(r"\bpdf\b|full\s*text|원문|전문", text):
                score += 50
            if re.search(r"download|다운로드", text):
                score += 40
            if score and element.tag_name.lower() == "a":
                score += 2
            if score:
                candidates.append((score, element, {"text": text[:200], "href": href[:500]}))
        except Exception:
            continue
    if not candidates:
        return None
    _, element, description = max(candidates, key=lambda item: item[0])
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", element)
        return description
    except Exception:
        return None


def save_ieee_viewer_pdf(driver, target):
    """Download the PDF already displayed by IEEE in this authenticated tab."""
    current = urlparse(driver.current_url)
    if current.hostname not in {"ieeexplore-ieee-org-ssl.libproxy.kyonggi.ac.kr", "ieeexplore.ieee.org"}:
        return False
    if current.path != "/stamp/stamp.jsp":
        return False
    driver.set_script_timeout(22)
    result = driver.execute_async_script("""
        const done = arguments[0];
        const frame = document.querySelector('iframe[src*="/stampPDF/getPDF.jsp"]');
        if (!frame || new URL(frame.src).origin !== location.origin) {
            done({error: "PDF viewer frame not found"});
            return;
        }
        fetch(frame.src, {credentials:"same-origin", mode:"same-origin",
                         signal:AbortSignal.timeout(18000)})
          .then(async response => {
            if (!response.ok) throw new Error("HTTP " + response.status);
            const blob = await response.blob();
            if (blob.size > 50 * 1024 * 1024) throw new Error("PDF exceeds 50 MiB");
            if (await blob.slice(0,5).text() !== "%PDF-") throw new Error("Response is not a PDF");
            const reader = new FileReader();
            reader.onload = () => done({data:reader.result.split(",", 2)[1]});
            reader.onerror = () => done({error:"PDF read failed"});
            reader.readAsDataURL(blob);
          }).catch(error => done({error:error.message}));
    """)
    if not result.get("data"):
        raise ValueError(result.get("error", "PDF viewer did not produce a file"))
    target.write_bytes(base64.b64decode(result["data"], validate=True))
    return True


def validate_downloads(paths, record):
    from pdf_handoff import verify_pdf

    verified, rejected = [], []
    for path in paths:
        try:
            verify_pdf(path, record)
        except (OSError, ValueError, RuntimeError) as error:
            rejected.append(str(error))
        else:
            verified.append(path)
    return verified, rejected


def automatic_institution_downloads(args: argparse.Namespace) -> int:
    """Navigate institutional links and click only visible PDF/download controls.

    The account owner performs login in Chrome.  This routine never receives
    credentials and never attempts CAPTCHA, paywall, or access-control bypass.
    """
    from selenium.common.exceptions import NoSuchWindowException

    records_path = Path(args.records)
    if not records_path.is_file():
        raise SystemExit(f"records file not found: {records_path}")
    raw_records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    target = Path(args.output_dir)
    pdf_dir = target / "institution_downloads"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    ranked_records = prioritize_records(raw_records, args.priority)
    export_priority_selection(ranked_records, target, args.priority)
    records = ranked_records[args.start_index : args.start_index + args.max_records]
    ledger_path = target / "institution_auto_download_ledger.jsonl"
    completed = set()
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            previous = json.loads(line)
            if previous.get("status") == "downloaded_verified" and all(
                (pdf_dir / name).is_file() for name in previous.get("files", [])
            ):
                completed.add(previous["candidate_id"])
    driver = build_driver(profile_dir(), reuse_open=args.reuse_open_chrome)
    prior_tab = driver.current_window_handle
    if args.reuse_open_chrome:
        driver.switch_to.new_window("tab")
    work_tab = driver.current_window_handle
    driver.set_page_load_timeout(30)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(pdf_dir.resolve())})
    if not args.reuse_open_chrome:
        driver.get(args.library_home)
        print("Chrome opened. Log in to Kyonggi Library/libproxy in this window.")
        input("After login is complete, press Enter here: ")
    saved = len(completed)
    processed = 0
    try:
        with ledger_path.open("a", encoding="utf-8") as ledger:
            for index, record in enumerate(records, start=args.start_index + 1):
                if args.target_downloads is not None and saved >= args.target_downloads:
                    break
                if record.get("candidate_id") in completed:
                    continue
                link = str(record.get("fulltext_url") or "")
                entry = {
                    "candidate_id": record.get("candidate_id"),
                    "title": record.get("title"),
                    "record_index": index,
                    "priority_rank": record.get("priority_rank"),
                    "priority_tier": record.get("priority_tier"),
                    "priority_score": record.get("priority_score"),
                    "opened_utc": utc_now(),
                }
                if not link:
                    entry["status"] = "skipped_no_institutional_link"
                else:
                    before = {item.name for item in pdf_dir.glob("*.pdf")}
                    opened_pdf_tab = None
                    try:
                        driver.get(link)
                        time.sleep(args.page_wait_seconds)
                        viewer_file = pdf_dir / pdf_filename(record)
                        added = newly_saved_pdfs(pdf_dir, before, 1)
                        if not added and viewer_file.name not in before and save_ieee_viewer_pdf(driver, viewer_file):
                            added = [viewer_file]
                        if not added:
                            known_tabs = set(driver.window_handles)
                            control = click_visible_pdf_control(driver)
                            if control is not None:
                                entry["clicked_control"] = control
                                time.sleep(args.page_wait_seconds)
                                new_tabs = set(driver.window_handles) - known_tabs
                                if len(new_tabs) == 1:
                                    opened_pdf_tab = new_tabs.pop()
                                    driver.switch_to.window(opened_pdf_tab)
                                if viewer_file.name not in before and save_ieee_viewer_pdf(driver, viewer_file):
                                    added = [viewer_file]
                                else:
                                    added = newly_saved_pdfs(pdf_dir, before, args.download_wait_seconds)
                        verified, rejected = validate_downloads(added, record)
                        if rejected:
                            entry["rejected"] = rejected
                        if len(verified) == 1:
                            item = verified[0]
                            entry.update(status="downloaded_verified", files=[item.name], bytes=item.stat().st_size)
                            saved += 1
                        elif verified:
                            entry["status"] = "ambiguous_multiple_verified_pdfs"
                        else:
                            entry["status"] = "no_verified_pdf"
                    except Exception as exc:
                        entry["status"] = f"failed_{type(exc).__name__}"
                        if isinstance(exc, ValueError):
                            entry["reason"] = str(exc)
                    finally:
                        if opened_pdf_tab and opened_pdf_tab in driver.window_handles:
                            try:
                                driver.switch_to.window(opened_pdf_tab)
                                driver.close()
                            except NoSuchWindowException:
                                pass
                        handles = driver.window_handles
                        if work_tab in handles:
                            driver.switch_to.window(work_tab)
                        elif handles:
                            driver.switch_to.window(handles[0])
                            driver.switch_to.new_window("tab")
                            work_tab = driver.current_window_handle
                            driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(pdf_dir.resolve())})
                processed += 1
                ledger.write(json.dumps(entry, ensure_ascii=False) + "\n")
                ledger.flush()
                print(f"Processed {processed}/{len(records)} links; PDFs saved: {saved}", flush=True)
                if args.target_downloads is not None and saved >= args.target_downloads:
                    break
                time.sleep(args.delay_seconds)
    finally:
        if args.reuse_open_chrome:
            if work_tab in driver.window_handles:
                try:
                    driver.switch_to.window(work_tab)
                    driver.close()
                except NoSuchWindowException:
                    pass
            if prior_tab in driver.window_handles:
                driver.switch_to.window(prior_tab)
        else:
            driver.quit()
    manifest = {
        "tool": "kyonggi-library-collector",
        "mode": "automatic-visible-institution-download",
        "priority_mode": args.priority,
        "source_records": str(records_path),
        "processed_records": processed,
        "pdfs_saved": saved,
        "target_downloads": args.target_downloads,
        "boundary": "The user signs in in Chrome. The tool follows visible PDF controls and saves an IEEE PDF displayed in the same session.",
    }
    (target / "institution_auto_download_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Complete: {saved} PDFs -> {pdf_dir.resolve()}")
    if args.target_downloads is not None and saved < args.target_downloads:
        print(f"Target not reached: {saved}/{args.target_downloads} verified PDFs.", file=sys.stderr)
        return 2
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manual-login Kyonggi Library metadata collector")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collect", help="Open Chrome, wait for manual login/search, export visible metadata")
    c.add_argument("--query", required=True, help="Research keyword recorded in the ledger")
    c.add_argument("--mode", choices=("direct", "browser"), default="direct", help="direct uses Kyonggi's public EDS result endpoint; browser uses a manual/live login session")
    c.add_argument("--library-home", default=LIBRARY_HOME)
    c.add_argument("--auto-login", action="store_true", help="Prompt locally for ID/password and fill the live login form; never stores credentials")
    c.add_argument("--login-url", help="Optional direct Kyonggi SSO/library login URL")
    c.add_argument("--username-selector", help="Optional CSS selector for the ID input")
    c.add_argument("--password-selector", help="Optional CSS selector for the password input")
    c.add_argument("--submit-selector", help="Optional CSS selector for the submit control")
    c.add_argument("--output-dir", default="outputs")
    c.add_argument("--max-pages", type=int, default=10)
    c.add_argument("--max-records", type=int, default=100)
    d = sub.add_parser("download-public", help="Download only direct public PDF responses referenced by an existing records.jsonl")
    d.add_argument("--records", required=True, help="Path to records.jsonl produced by collect")
    d.add_argument("--output-dir", required=True, help="Directory for public_pdfs and download ledger")
    d.add_argument("--max-attempts", type=int, default=100)
    d.add_argument("--max-downloads", type=int, default=100)
    d.add_argument("--max-mb", type=int, default=75)
    d.add_argument("--delay-seconds", type=float, default=1.0)
    d.add_argument("--timeout-seconds", type=float, default=8.0, help="Per-link network timeout; slow providers are logged and skipped")
    d.add_argument("--start-index", type=int, default=0, help="Zero-based record offset; lets an interrupted run continue")
    i = sub.add_parser("review-downloads", help="Open institutional links one-by-one after manual login; record PDFs saved by the user")
    i.add_argument("--records", required=True, help="Path to records.jsonl produced by collect")
    i.add_argument("--output-dir", required=True, help="Directory for user-approved institutional PDFs and ledger")
    i.add_argument("--library-home", default=LIBRARY_HOME)
    i.add_argument("--max-records", type=int, default=100)
    i.add_argument("--start-index", type=int, default=0)
    i.add_argument("--download-wait-seconds", type=int, default=20, help="Wait after user confirmation for Chrome to finish a PDF")
    a = sub.add_parser("auto-downloads", help="After manual login, download and verify PDFs from institutional links")
    a.add_argument("--records", required=True, help="Path to records.jsonl produced by collect")
    a.add_argument("--output-dir", required=True, help="Directory for downloaded PDFs and ledger")
    a.add_argument("--library-home", default=LIBRARY_HOME)
    a.add_argument("--max-records", type=int, default=100)
    a.add_argument("--start-index", type=int, default=0)
    a.add_argument("--page-wait-seconds", type=int, default=3)
    a.add_argument("--download-wait-seconds", type=int, default=20)
    a.add_argument("--delay-seconds", type=float, default=1.0)
    a.add_argument("--reuse-open-chrome", action="store_true", help="Reuse the collector's already signed-in Chrome")
    a.add_argument("--target-downloads", type=int, help="Stop after this many verified PDFs")
    a.add_argument("--priority", choices=("top-tier", "source-order"), default="top-tier", help="top-tier ranks recognized security venues and reputable journals before general results")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.command == "download-public":
        if args.max_attempts < 1 or args.max_downloads < 1 or args.max_mb < 1 or args.delay_seconds < 0 or args.timeout_seconds <= 0 or args.start_index < 0:
            raise SystemExit("Download limits must be positive (delay-seconds may be zero).")
        return download_public_pdfs(args)
    if args.command == "review-downloads":
        if args.max_records < 1 or args.start_index < 0 or args.download_wait_seconds < 1:
            raise SystemExit("Review download limits must be positive.")
        return browser_assisted_downloads(args)
    if args.command == "auto-downloads":
        if args.target_downloads is not None and args.target_downloads < 1:
            raise SystemExit("target-downloads must be positive.")
        if args.max_records < 1 or args.start_index < 0 or args.download_wait_seconds < 1 or args.page_wait_seconds < 0 or args.delay_seconds < 0:
            raise SystemExit("Automatic download limits must be positive (wait and delay values may be zero where applicable).")
        return automatic_institution_downloads(args)
    if args.max_pages < 1 or args.max_records < 1 or args.max_records > 1000:
        raise SystemExit("max-pages must be >= 1 and max-records must be 1..1000.")
    if args.mode == "direct":
        if args.auto_login:
            raise SystemExit("--auto-login requires --mode browser. Default direct mode collects Kyonggi EDS metadata without login.")
        return collect_direct(args)
    return collect(args)


if __name__ == "__main__":
    raise SystemExit(main())
