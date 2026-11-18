"""Stage Windows downloads and verify their hashes on the Ubuntu side."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory
import unicodedata

from local_research_pipeline import pdf_sha256, read_jsonl, write_jsonl


METADATA_FIELDS = (
    "candidate_id", "title", "authors", "doi", "year", "publication_source",
    "local_selection_reason", "priority_reason",
)


def child_file(directory, filename):
    if not filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Expected a file name, got {filename!r}")
    path = directory / filename
    if path.is_symlink() or not path.is_file() or path.resolve().parent != directory.resolve():
        raise ValueError(f"Missing or invalid file: {path}")
    return path


def normalized_title(text):
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())


def verify_pdf(path, record):
    import pymupdf

    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError(f"Invalid PDF header: {path.name}")
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError(f"PDF exceeds the archive tool's 50 MiB limit: {path.name}")
    with pymupdf.open(path) as pdf:
        if pdf.needs_pass or not pdf.page_count:
            raise ValueError(f"Unreadable PDF: {path.name}")
        first_page = pdf[0].get_text()
        title = normalized_title(str(record.get("title") or ""))
        doi = re.sub(r"(?i)^(https?://(?:dx\.)?doi\.org/|doi:\s*)", "", str(record.get("doi") or "").strip())
        doi_in_page = doi and re.search(r"(?<![\w/])" + re.escape(doi) + r"(?![\w./-])", first_page, re.I)
        if doi_in_page:
            return "first_page_doi"
        if len(title) >= 12 and title in normalized_title(first_page):
            return "first_page_title"
        raise ValueError(f"Review the PDF's title or DOI: {path.name}")


def stage(records_path, download_ledger, output):
    records = {row["candidate_id"]: row for row in read_jsonl(records_path)}
    entries = [row for row in read_jsonl(download_ledger) if row.get("files")]
    ids = Counter(row["candidate_id"] for row in entries)
    filenames = Counter(name for row in entries for name in row["files"])
    download_dir = download_ledger.parent / "institution_downloads"
    if output.exists():
        raise ValueError(f"Batch already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    accepted, held = [], []
    with TemporaryDirectory(dir=output.parent, prefix=".pdf-staging-") as temporary:
        batch = Path(temporary) / output.name
        pdf_dir = batch / "pdfs"
        pdf_dir.mkdir(parents=True)
        for row in entries:
            candidate = row["candidate_id"]
            try:
                if candidate not in records or not re.fullmatch(r"(?a)[A-Za-z0-9][A-Za-z0-9_-]*", candidate):
                    raise ValueError("Unknown or unsafe candidate ID")
                if ids[candidate] != 1 or len(row["files"]) != 1 or filenames[row["files"][0]] != 1:
                    raise ValueError("Ambiguous PDF-to-candidate assignment")
                source = child_file(download_dir, row["files"][0])
                filename = candidate + ".pdf"
                target = pdf_dir / filename
                shutil.copyfile(source, target)
                try:
                    identity = verify_pdf(target, records[candidate])
                except (ValueError, RuntimeError):
                    target.unlink(missing_ok=True)
                    raise
                metadata = {key: records[candidate][key] for key in METADATA_FIELDS if key in records[candidate]}
                accepted.append(dict(metadata, pdf_filename=filename, sha256=pdf_sha256(target), identity=identity))
            except (ValueError, RuntimeError) as error:
                held.append(f"{candidate}: {error}")
        for problem in held:
            print(f"Held for review: {problem}")
        if not accepted:
            raise ValueError("No verified PDF could be staged")
        write_jsonl(batch / "records.jsonl", accepted)
        batch.rename(output)
    print(f"Staged {len(accepted)} verified PDF(s) at {output}; held {len(held)}.")


def verify(batch):
    rows = read_jsonl(batch / "records.jsonl")
    if not rows:
        raise ValueError("Batch is empty")
    for row in rows:
        pdf = child_file(batch / "pdfs", row["pdf_filename"])
        if pdf_sha256(pdf) != row["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {pdf.name}")
        verify_pdf(pdf, row)
    print(f"Verified {len(rows)} PDF(s): {batch}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pack = sub.add_parser("stage")
    pack.add_argument("records", type=Path)
    pack.add_argument("download_ledger", type=Path)
    pack.add_argument("batch", type=Path)
    check = sub.add_parser("verify")
    check.add_argument("batch", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "stage":
            stage(args.records, args.download_ledger, args.batch)
        else:
            verify(args.batch)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
