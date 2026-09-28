"""Versioned venue classification and official accepted-paper collectors.

The ACL/OpenReview collection approach is adapted from LikeACloud7/ai-trend
(MIT, revision e20dfc1eebff33c0ce635f26be70cce82ae6bacd).  The records are
reclassified here against an explicit historical BK21+ baseline; the upstream
project's conference selection is never treated as a quality judgement.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from .core import now


BK21_2018_SOURCE = (
    "https://cse.skku.edu/cse/notice_grad.do?articleNo=210824&attachNo=181782&mode=download"
)
BK21_2018 = {
    "acl": ("ACL", 4, "Top-tier", "ai"),
    "icml": ("ICML", 4, "Top-tier", "ai"),
    "neurips": ("NIPS", 4, "Top-tier", "ai"),
    "emnlp": ("EMNLP", 3, "Top-tier", "ai"),
    "naacl": ("NAACL/HLT", 2, "2nd-Tier", "ai"),
    "ccs": ("CCS", 4, "Top-tier", "cybersecurity"),
    "sp": ("S&P", 4, "Top-tier", "cybersecurity"),
    "usenix_security": ("Security", 3, "Top-tier", "cybersecurity"),
    "ndss": ("NDSS", 2, "2nd-Tier", "cybersecurity"),
}

VENUES = {
    "acl": {"name": "ACL", "track": "ai", "provider": "acl", "event": "acl", "suffixes": ("long", "short", "main")},
    "emnlp": {"name": "EMNLP", "track": "ai", "provider": "acl", "event": "emnlp", "suffixes": ("main", "long", "short")},
    "naacl": {"name": "NAACL", "track": "ai", "provider": "acl", "event": "naacl", "suffixes": ("main", "long", "short")},
    "iclr": {"name": "ICLR", "track": "ai", "provider": "openreview", "prefix": "ICLR.cc"},
    "icml": {"name": "ICML", "track": "ai", "provider": "openreview", "prefix": "ICML.cc"},
    "neurips": {"name": "NeurIPS", "track": "ai", "provider": "openreview", "prefix": "NeurIPS.cc"},
    # Classification is ready, but official collectors for these venues are a later milestone.
    "ccs": {"name": "ACM CCS", "track": "cybersecurity", "provider": "pending"},
    "sp": {"name": "IEEE S&P", "track": "cybersecurity", "provider": "pending"},
    "usenix_security": {"name": "USENIX Security", "track": "cybersecurity", "provider": "pending"},
    "ndss": {"name": "NDSS", "track": "cybersecurity", "provider": "pending"},
}


def classify_venue(venue: str, publication_type: str = "regular") -> dict:
    """Return the historical list entry and paper-type application separately."""
    key = venue.strip().lower()
    row = BK21_2018.get(key)
    base = {
        "baseline": "BK21+ Computer Science 우수국제학술대회 목록",
        "baseline_date": "2018-03-01",
        "baseline_source": BK21_2018_SOURCE,
        "latest_official_status": "확인 불가: 2018 역사적 기준선이며 현재 연구실 적용 기준은 별도 확인 필요",
    }
    if row is None:
        return {**base, "listed": False, "list_name": None, "tier": "목록 미등재", "base_if": None,
                "publication_type": publication_type, "application_status": "판정 보류", "effective_if": None,
                "top_tier_eligible": False}
    list_name, base_if, tier, track = row
    application = "regular 인정 기준"
    effective = base_if
    if publication_type == "short":
        application, effective = "Short: 인정 IF 1점 차감", max(0, base_if - 1)
    elif publication_type == "spotlight":
        application, effective = "Spotlight: 인정 IF 2점 차감", max(0, base_if - 2)
    elif publication_type in {"poster", "workshop"}:
        application, effective = "워크숍·포스터: IF 미부여", None
    elif publication_type in {"findings", "accepted_unspecified"}:
        application, effective = "논문 유형을 Regular로 확정하기 전 판정 보류", None
    return {**base, "listed": True, "list_name": list_name, "tier": tier, "base_if": base_if,
            "baseline_track": track, "publication_type": publication_type,
            "application_status": application, "effective_if": effective,
            "top_tier_eligible": tier == "Top-tier" and effective is not None}


def _clean(value) -> str:
    value = str(value or "")
    # Inline formatting must not split tokens (for example ``LLM<span>s</span>``).
    value = re.sub(r"</?(?:span|em|i|b|strong|sup|sub)\b[^>]*>", "", value, flags=re.I)
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"(?<=\w)\s*([-–—])\s*(?=\w)", r"\1", value)
    return re.sub(r"\s+([,.;:!?%])", r"\1", value)


def _value(field, fallback=""):
    return field.get("value", fallback) if isinstance(field, dict) else (field if field is not None else fallback)


def _list(field) -> list[str]:
    value = _value(field, [])
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value).strip()] if str(value).strip() else []


def relevance(paper: dict, query: str) -> dict:
    """Transparent lexical relevance for candidate selection, never a quality score."""
    terms = [x for x in re.findall(r"[\w-]+", query.lower()) if len(x) > 1]
    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()
    keywords = " ".join(paper.get("keywords") or []).lower()
    matched = [term for term in terms if term in title or term in abstract or term in keywords]
    return {"query_terms": terms, "matched_terms": sorted(set(matched)),
            "relevance_score": sum(5 for t in terms if t in title) + sum(2 for t in terms if t in keywords) + sum(1 for t in terms if t in abstract),
            "score_note": "검색 후보 정렬용 어휘 일치값이며 논문 품질 점수나 BK21 등급이 아님"}


@dataclass
class VenueCollector:
    run: object
    timeout: float = 30
    max_source_records: int = 5000

    async def _get_text(self, url: str, params: dict | None = None) -> str:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False, trust_env=False,
                                     headers={"User-Agent": "root-paper-lab/0.2 (research audit)"}) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.text

    def _archive_source(self, name: str, url: str, body: str, content_type: str) -> None:
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.run.write(f"sources/{name}", body)
        self.run.event("official_source_snapshot", {"url": url, "retrieved_utc": now(),
            "sha256": digest, "content_type": content_type, "file": f"sources/{name}"})

    async def collect(self, venue: str, year: int) -> tuple[list[dict], dict]:
        config = VENUES.get(venue)
        if config is None:
            raise ValueError(f"unsupported venue: {venue}")
        if config["provider"] == "pending":
            return [], {"venue": venue, "year": year, "status": "collector_not_implemented",
                        "official_publication_verified": False}
        if config["provider"] == "acl":
            return await self._collect_acl(venue, config, year)
        return await self._collect_openreview(venue, config, year)

    async def _collect_acl(self, venue: str, config: dict, year: int) -> tuple[list[dict], dict]:
        url = f"https://aclanthology.org/events/{config['event']}-{year}/"
        body = await self._get_text(url)
        self._archive_source(f"{venue}-{year}.html", url, body, "text/html")
        volume_pattern = re.compile(r"href=/volumes/([^/]+)/>([\s\S]*?)</a>")
        volumes = []
        for volume_id, title in volume_pattern.findall(body):
            prefix = f"{year}.{config['event']}-"
            suffix = volume_id[len(prefix):] if volume_id.startswith(prefix) else ""
            if suffix in config["suffixes"]:
                volumes.append((volume_id, suffix, "main"))
            elif volume_id == f"{year}.findings-{config['event']}":
                volumes.append((volume_id, "findings", "findings"))
        papers = []
        for volume_id, subtype, track in volumes:
            marker = f"<div id={volume_id.replace('.', '')}>"
            start = body.find(marker)
            if start < 0:
                continue
            end = body.find("<hr><div id=", start + len(marker))
            section = body[start:end if end >= 0 else None]
            matches = list(re.finditer(r"<strong><a class=align-middle href=/([0-9]{4}\.[^/]+?\.\d+)/>([\s\S]*?)</a></strong><br>", section))
            for index, match in enumerate(matches):
                pid, raw_title = match.groups()
                chunk_end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
                chunk = section[match.start():chunk_end]
                author_part = chunk.partition("</strong><br>")[2].partition("</span></div>")[0]
                authors = [_clean(x) for x in re.findall(r"<a[^>]*>([\s\S]*?)</a>", author_part)]
                abstract_match = re.search(r'<div class="card-body p-3 small">([\s\S]*?)</div></div>', chunk)
                ptype = "findings" if track == "findings" else ("short" if subtype == "short" else "regular")
                title = _clean(raw_title).removesuffix(" Download PDF").strip()
                if title and not re.match(r"^(proceedings|front matter|preface|table of contents)", title, re.I):
                    papers.append({"paperId": pid, "title": title, "authors": authors, "abstract": _clean(abstract_match.group(1) if abstract_match else ""),
                        "year": year, "venue_key": venue, "venue": config["name"], "publication_type": ptype,
                        "official_source": "ACL Anthology", "official_url": f"https://aclanthology.org/{pid}/",
                        "official_publication_status": "공식 색인 스냅샷에서 확인", "keywords": []})
        truncated = len(papers) > self.max_source_records
        papers = papers[:self.max_source_records]
        return papers, {"venue": venue, "year": year, "status": "partial" if truncated else "ok",
                        "source": "ACL Anthology", "url": url, "papers": len(papers), "truncated": truncated}

    async def _collect_openreview(self, venue: str, config: dict, year: int) -> tuple[list[dict], dict]:
        endpoint = "https://api2.openreview.net/notes"
        venue_id = f"{config['prefix']}/{year}/Conference"
        notes, offset = [], 0
        while len(notes) < self.max_source_records:
            params = {"content.venueid": venue_id, "limit": min(1000, self.max_source_records - len(notes)), "offset": offset}
            body = await self._get_text(endpoint, params)
            url = endpoint + "?" + urlencode(params)
            self._archive_source(f"{venue}-{year}-{offset}.json", url, body, "application/json")
            page = json.loads(body).get("notes") or []
            notes.extend(page)
            if len(page) < params["limit"]:
                break
            offset += len(page)
        papers = []
        for note in notes:
            content = note.get("content") or {}
            title = _clean(_value(content.get("title")))
            venue_text = _clean(_value(content.get("venue"))).lower()
            ptype = next((x for x in ("oral", "spotlight", "poster") if x in venue_text), "accepted_unspecified")
            if ptype == "oral":
                ptype = "regular"
            if title:
                papers.append({"paperId": note.get("id"), "title": title, "authors": _list(content.get("authors")),
                    "abstract": _clean(_value(content.get("abstract"))), "year": year, "venue_key": venue,
                    "venue": config["name"], "publication_type": ptype, "official_source": "OpenReview",
                    "official_url": f"https://openreview.net/forum?id={note.get('id')}",
                    "official_publication_status": "공식 OpenReview venue ID에서 확인", "keywords": _list(content.get("keywords"))})
        truncated = len(notes) >= self.max_source_records
        return papers, {"venue": venue, "year": year, "status": "partial" if truncated else ("ok" if papers else "empty"),
                        "source": "OpenReview", "venue_id": venue_id, "papers": len(papers), "truncated": truncated}
