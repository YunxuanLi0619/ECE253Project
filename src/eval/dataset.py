"""Own-capture dataset: metadata CSV + image dir + PDF dir, checked against the capture protocol."""
import csv
import os
import random
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .groundtruth import pdf_ground_truth
from .metrics import score
from .normalize import normalize

CONDITIONS = ("clean", "blur", "shadow", "persp", "combo")
PER_PAGE_COUNTS = {"clean": 1, "blur": 3, "shadow": 3, "persp": 3, "combo": 2}
DOC_TYPES = ("paper", "book", "table", "receipt")
CSV_FIELDS = (
    "filename", "page_id", "doc_type", "condition", "seq", "phone_model", "light", "angle_deg",
    "blur_dir", "shadow_type", "split", "captured_at", "resolution", "pilot", "notes",
    "pdf_file", "pdf_page",
)
MIN_GT_CHARS = 100
# Word error rate between pdftotext's default order and -layout (row-wise) order above which
# a table page is suspected of having a scrambled reading order.
TABLE_ORDER_WER = 0.3

SPLIT_SEED = 253
SPLITS = ("tuning", "test")

FILENAME_RE = re.compile(r"^p(\d+)_([^_./]+)_(\d+)\.jpg$")
PAGE_ID_RE = re.compile(r"^p?(\d+)$")
FILENAME_FORMAT = "p<页>_<条件>_<序号>.jpg"


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    n_images: int = 0
    n_pages: int = 0


def read_rows(csv_path: Path) -> tuple[list[str], list[dict]]:
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def page_label(page_id: str) -> str | None:
    m = PAGE_ID_RE.match(page_id.strip())
    return f"p{int(m.group(1)):02d}" if m else None


def validate_dataset(csv_path: Path, images_dir: Path, pdf_dir: Path,
                     min_chars: int = MIN_GT_CHARS) -> Report:
    rep = Report()
    columns, rows = read_rows(csv_path)
    missing = [c for c in CSV_FIELDS if c not in columns]
    if missing:
        rep.errors.append(f"CSV is missing required column(s): {', '.join(missing)}")
        return rep

    on_disk = {p.name for p in images_dir.iterdir() if p.is_file() and not p.name.startswith(".")}
    seen: dict[str, int] = {}
    pages: dict[str, list[dict]] = defaultdict(list)

    for line, row in enumerate(rows, start=2):  # line 1 is the header
        name = row["filename"].strip()
        where = f"CSV line {line} ({name})"
        if name in seen:
            rep.errors.append(f"{where}: duplicate filename, first seen on line {seen[name]}")
            continue
        seen[name] = line
        rep.n_images += 1
        if name not in on_disk:
            rep.errors.append(f"{where}: image file missing from {images_dir}")

        m = FILENAME_RE.match(name)
        if not m:
            rep.errors.append(f"{where}: filename does not match {FILENAME_FORMAT}")
        elif m.group(2) not in CONDITIONS:
            rep.errors.append(
                f"{where}: unknown condition '{m.group(2)}' in filename, expected one of "
                f"{', '.join(CONDITIONS)}")

        cond = row["condition"].strip()
        if cond not in CONDITIONS:
            rep.errors.append(
                f"{where}: unknown condition '{cond}' in CSV, expected one of {', '.join(CONDITIONS)}")
        label = page_label(row["page_id"])
        if label is None:
            rep.errors.append(f"{where}: bad page_id '{row['page_id']}'")
        if m:
            if m.group(2) in CONDITIONS and cond in CONDITIONS and m.group(2) != cond:
                rep.errors.append(f"{where}: condition '{cond}' in CSV disagrees with filename")
            if label is not None and page_label(m.group(1)) != label:
                rep.errors.append(f"{where}: page_id '{row['page_id']}' disagrees with filename")
            if row["seq"].strip() != str(int(m.group(3))):
                rep.errors.append(f"{where}: seq '{row['seq']}' disagrees with filename")
        if row["doc_type"].strip() not in DOC_TYPES:
            rep.errors.append(
                f"{where}: unknown doc_type '{row['doc_type'].strip()}', expected one of "
                f"{', '.join(DOC_TYPES)}")
        if label is not None:
            pages[label].append(row)

    for name in sorted(on_disk - set(seen)):
        rep.errors.append(f"image {name}: no CSV row")

    rep.n_pages = len(pages)
    for label in sorted(pages):
        _check_page(rep, label, pages[label], pdf_dir, min_chars)
    return rep


def _check_page(rep: Report, label: str, rows: list[dict], pdf_dir: Path, min_chars: int) -> None:
    for cond, expected in PER_PAGE_COUNTS.items():
        got = sum(1 for r in rows if r["condition"].strip() == cond)
        if got != expected:
            rep.errors.append(f"page {label}: condition {cond} has {got} image(s), expected {expected}")

    doc_types = {r["doc_type"].strip() for r in rows}
    if len(doc_types) > 1:
        rep.errors.append(f"page {label}: rows disagree on doc_type: {', '.join(sorted(doc_types))}")

    gt = _ground_truth(rep, label, rows, pdf_dir)
    if gt is None:
        return
    text, pdf, pdf_page = gt
    if not text:
        rep.warnings.append(f"page {label}: text layer is empty ({pdf} p.{pdf_page}), replace this page")
    elif len(text) < min_chars:
        rep.warnings.append(
            f"page {label}: text layer is short ({len(text)} chars < {min_chars}; {pdf} p.{pdf_page})")
    if text and doc_types == {"table"} and _reading_order_suspect(pdf_dir / pdf, pdf_page, text):
        rep.warnings.append(
            f"page {label}: table reading order looks scrambled ({pdf} p.{pdf_page}), consider replacing")


def _page_link(rep: Report, label: str, rows: list[dict]) -> tuple[str, int] | None:
    files = {r["pdf_file"].strip() for r in rows}
    pages = {r["pdf_page"].strip() for r in rows}
    if len(files) > 1 or len(pages) > 1:
        rep.errors.append(
            f"page {label}: rows disagree on source PDF: pdf_file {sorted(files)}, pdf_page {sorted(pages)}")
        return None
    pdf, page = files.pop(), pages.pop()
    if not pdf:
        rep.errors.append(f"page {label}: no source PDF (pdf_file is empty)")
        return None
    if not page.isdigit() or int(page) < 1:
        rep.errors.append(f"page {label}: pdf_page '{page}' is not a 1-based page number")
        return None
    return pdf, int(page)


def _ground_truth(rep: Report, label: str, rows: list[dict], pdf_dir: Path):
    link = _page_link(rep, label, rows)
    if link is None:
        return None
    pdf, page = link
    if not (pdf_dir / pdf).is_file():
        rep.errors.append(f"page {label}: source PDF {pdf} not found in {pdf_dir}")
        return None
    try:
        raw = pdf_ground_truth(pdf_dir / pdf, page)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        detail = (getattr(e, "stderr", "") or str(e)).strip().splitlines()
        rep.errors.append(
            f"page {label}: cannot extract ground truth from {pdf} p.{page}: "
            f"{detail[0] if detail else 'pdftotext failed'}")
        return None
    return normalize(raw), pdf, page


def _reading_order_suspect(pdf: Path, page: int, default_text: str) -> bool:
    """pdftotext's default order vs its -layout (row-wise) order of the same page."""
    layout = subprocess.run(
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
        capture_output=True, text=True, check=True).stdout
    layout = normalize(layout)
    if not layout:
        return False
    return score(layout, default_text).wer > TABLE_ORDER_WER


class SplitError(Exception):
    """The split cannot be made (or must not be redone); the message says why."""


@dataclass
class SplitResult:
    side_of: dict[str, str]  # page label -> "tuning" | "test"
    types: dict[str, str]  # page label -> doc_type
    phones: dict[str, str]  # page label -> phone_model ("" when unknown)


def _is_pilot(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def tuning_quota(n_pages: int) -> int:
    """About a third of a type's pages go to tuning; 12/24 overall for the 36-page corpus
    (paper 12 -> 4, book 10 -> 3, table 8 -> 3, receipt 6 -> 2)."""
    return round(n_pages / 3)


def split_dataset(csv_path: Path) -> SplitResult:
    """Assign every page to the tuning or test set and write it into the CSV's split column.

    Stratified by doc_type, seeded with SPLIT_SEED, pilot pages forced into tuning. Refuses to
    run when any row already carries a split: the split is made once and never redrawn."""
    columns, rows = read_rows(csv_path)
    if "split" not in columns:
        raise SplitError("CSV has no 'split' column")
    if any(r["split"].strip() for r in rows):
        raise SplitError(
            f"{csv_path} already has a split; it is made once and never overwritten "
            "(tuning must not leak into testing)")

    pages: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    errors = []
    for line, row in enumerate(rows, start=2):
        label = page_label(row["page_id"])
        if label is None:
            errors.append(f"CSV line {line} ({row['filename']}): bad page_id '{row['page_id']}'")
            continue
        if row["doc_type"].strip() not in DOC_TYPES:
            errors.append(
                f"CSV line {line} ({row['filename']}, page {label}): unknown doc_type "
                f"'{row['doc_type'].strip()}', expected one of {', '.join(DOC_TYPES)}")
        pages[label].append((line, row))
    by_type: dict[str, list[str]] = defaultdict(list)
    for label, items in pages.items():
        doc_types = {r["doc_type"].strip() for _, r in items}
        if len(doc_types) > 1:
            errors.append(f"page {label}: rows disagree on doc_type: {', '.join(sorted(doc_types))}")
        by_type[doc_types.pop() if len(doc_types) == 1 else ""].append(label)
    by_type.pop("", None)
    if errors:
        raise SplitError("\n".join(errors))

    rng = random.Random(SPLIT_SEED)
    side_of: dict[str, str] = {}
    for doc_type in DOC_TYPES:  # fixed order, so the draw does not depend on the input order
        labels = sorted(by_type.get(doc_type, []))
        if not labels:
            continue
        if len(labels) < 2:
            raise SplitError(
                f"doc_type {doc_type} has {len(labels)} page(s); need at least 2 to put it on both sides")
        quota = tuning_quota(len(labels))
        pilots = [p for p in labels if any(_is_pilot(r["pilot"]) for _, r in pages[p])]
        if len(pilots) > quota:
            raise SplitError(
                f"doc_type {doc_type}: {len(pilots)} pilot pages ({', '.join(pilots)}) but only "
                f"{quota} tuning slots of {len(labels)} pages; pilot pages must be in the tuning set")
        rest = [p for p in labels if p not in pilots]
        rng.shuffle(rest)
        tuning = set(pilots) | set(rest[:quota - len(pilots)])
        for p in labels:
            side_of[p] = "tuning" if p in tuning else "test"

    for label, items in pages.items():
        for _, row in items:
            row["split"] = side_of[label]
    tmp = csv_path.with_name(csv_path.name + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, csv_path)

    types = {p: r[0][1]["doc_type"].strip() for p, r in pages.items()}
    phones = {p: next((r["phone_model"].strip() for _, r in items if r["phone_model"].strip()), "")
              for p, items in pages.items()}
    return SplitResult(side_of, types, phones)
