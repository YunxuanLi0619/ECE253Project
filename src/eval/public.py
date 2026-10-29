"""Public-dataset tables, one per reference source (ADR-0002).

  <root>/smartdoc_qa/manifest.csv  filename, page_id, doc_class, distortion, reference
                      images/<filename>, transcriptions/<reference>   -> reference: human transcription
  <root>/rdd/manifest.csv          filename, page_id, condition (clean | shadow)
                      images/<filename>                               -> reference: pseudo ground truth

Reference texts all go through the shared `normalize`. RDD has no text: the reference of a scene's shadow
images is the OCR of that scene's clean image. Each dataset gets its own report file; the sources are never
pooled into one table."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .baseline import ReportError, _ocr_upright, _save_json
from .dataset import read_rows
from .metrics import score
from .normalize import NORMALIZE_VERSION, normalize
from .ocr import OCR_CONFIG, tesseract_version
from .report import MIN_PAGES_FOR_CI, _cell, _fmt_cell, _page_means

CACHE_FILE = "public_ocr_cache.json"
PSEUDO_GT = "pseudo ground truth, relative improvement only"
HUMAN = "human transcription"
RDD_COLUMN = "all"
SMARTDOC_COLUMNS = ("filename", "page_id", "doc_class", "distortion", "reference")
RDD_COLUMNS = ("filename", "page_id", "condition")
RDD_CONDITIONS = ("clean", "shadow")


@dataclass
class PublicResult:
    dataset: str
    reference: str  # label printed in the table header
    header: dict
    records: list[dict]  # one per scored image
    columns: list[str]
    conditions: list[str]
    cells: dict  # metric -> condition -> column -> cell
    markdown: str


class OcrSource:
    """Raw OCR text per image: from a precomputed JSON, or from Tesseract with a result cache."""

    def __init__(self, precomputed: Path | None, out_dir: Path):
        self.precomputed = (json.loads(precomputed.read_text(encoding="utf-8"))
                            if precomputed is not None else None)
        self.cache_path = out_dir / CACHE_FILE
        self.header = ({"ocr": f"precomputed from {precomputed.name}", "normalize_version": NORMALIZE_VERSION}
                       if precomputed is not None else
                       {"tesseract": tesseract_version(), "ocr_config": OCR_CONFIG,
                        "normalize_version": NORMALIZE_VERSION})
        self.cache: dict[str, dict] = {}
        self.dirty = False
        if precomputed is None and self.cache_path.is_file():
            try:
                stored = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if stored["header"] == self.header:
                    self.cache = stored["images"]
            except (ValueError, KeyError, TypeError):
                pass
        self.n_ocr = self.n_cached = 0

    def text(self, key: str, path: Path) -> str:
        if self.precomputed is not None:
            if key not in self.precomputed:
                raise ReportError(f"precomputed OCR text lacks image {key}")
            return self.precomputed[key]
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        entry = self.cache.get(key)
        if entry and entry["sha256"] == sha:
            self.n_cached += 1
            return entry["text"]
        text = _ocr_upright(path)
        self.cache[key] = {"sha256": sha, "text": text}
        self.n_ocr += 1
        self.dirty = True
        return text

    def save(self) -> None:
        if self.precomputed is None and self.dirty:
            _save_json(self.cache_path, {"header": self.header, "images": self.cache})


def _read_manifest(dataset: str, d: Path, required: tuple[str, ...]) -> list[dict]:
    path = d / "manifest.csv"
    if not path.is_file():
        raise ReportError(f"{dataset}: manifest.csv not found in {d}")
    columns, rows = read_rows(path)
    missing = [c for c in required if c not in columns]
    if missing:
        raise ReportError(f"{dataset}/manifest.csv lacks column(s): {', '.join(missing)}")
    if not rows:
        raise ReportError(f"{dataset}/manifest.csv has no rows")
    for r in rows:
        if not (d / "images" / r["filename"]).is_file():
            raise ReportError(f"{dataset}: image {r['filename']} not found in {d / 'images'}")
    return rows


def _scored(rows_meta: list[dict], reference: str, hypothesis: str, **extra) -> dict:
    s = score(reference, normalize(hypothesis))
    return {**rows_meta, **extra, "cer": s.cer, "wer": s.wer, "char_N": s.char_N, "word_N": s.word_N}


def _smartdoc_records(d: Path, ocr: OcrSource) -> list[dict]:
    records = []
    for r in _read_manifest("smartdoc_qa", d, SMARTDOC_COLUMNS):
        ref_path = d / "transcriptions" / r["reference"]
        if not ref_path.is_file():
            raise ReportError(f"smartdoc_qa: transcription {r['reference']} (for {r['filename']}) "
                              f"not found in {d / 'transcriptions'}")
        reference = normalize(ref_path.read_text(encoding="utf-8"))
        if not reference:
            raise ReportError(f"smartdoc_qa: transcription {r['reference']} is empty")
        hyp = ocr.text(f"smartdoc_qa/{r['filename']}", d / "images" / r["filename"])
        records.append(_scored(
            {"filename": r["filename"], "page_id": r["page_id"].strip(), "doc_type": r["doc_class"].strip(),
             "condition": r["distortion"].strip()}, reference, hyp))
    return records


def _rdd_records(d: Path, ocr: OcrSource) -> list[dict]:
    rows = _read_manifest("rdd", d, RDD_COLUMNS)
    clean_of: dict[str, str] = {}
    for r in rows:
        cond, scene = r["condition"].strip(), r["page_id"].strip()
        if cond not in RDD_CONDITIONS:
            raise ReportError(f"rdd: {r['filename']} has unknown condition '{cond}' "
                              f"(expected {' / '.join(RDD_CONDITIONS)})")
        if cond == "clean":
            if scene in clean_of:
                raise ReportError(f"rdd: scene {scene} has more than one clean image")
            clean_of[scene] = r["filename"]
    pseudo: dict[str, str] = {}
    records = []
    for r in rows:
        scene = r["page_id"].strip()
        if r["condition"].strip() != "shadow":
            continue
        if scene not in clean_of:
            raise ReportError(f"rdd: scene {scene} ({r['filename']}) has no clean image to give the pseudo ground truth")
        if scene not in pseudo:
            name = clean_of[scene]
            pseudo[scene] = normalize(ocr.text(f"rdd/{name}", d / "images" / name))
            if not pseudo[scene]:
                raise ReportError(f"rdd: OCR of the clean image {name} (scene {scene}) is empty, "
                                  "no pseudo ground truth")
        hyp = ocr.text(f"rdd/{r['filename']}", d / "images" / r["filename"])
        records.append(_scored(
            {"filename": r["filename"], "page_id": scene, "doc_type": RDD_COLUMN, "condition": "shadow"},
            pseudo[scene], hyp))
    if not records:
        raise ReportError("rdd: no shadow images in the manifest")
    return records


def _aggregate(records: list[dict]) -> tuple[list[str], list[str], dict]:
    columns = sorted({r["doc_type"] for r in records}, key=[r["doc_type"] for r in records].index)
    conditions = sorted({r["condition"] for r in records})
    cells = {}
    for metric in ("cer", "wer"):
        pages = _page_means(records, metric)
        cells[metric] = {
            cond: {col: _cell([v for (c, _), (t, v) in pages.items() if c == cond and t == col])
                   for col in columns}
            for cond in conditions}
    return columns, conditions, cells


def _render(title: str, note: str, reference: str, column_label: str, columns: list[str],
            conditions: list[str], cells: dict, header: dict) -> str:
    out = [f"# {title}", "", note, "", "## Evaluation Configuration", ""]
    out += [f"- {k}: {v}" for k, v in header.items()]
    for metric in ("cer", "wer"):
        out += ["", f"## {metric.upper()} (reference: {reference})", "",
                f"Cells are page-level macro-averages (first average the images of the same page and condition, then average over pages); n = number of pages; "
                f"a by-page bootstrap 95% interval is given only for n ≥ {MIN_PAGES_FOR_CI}.", ""]
        out += [f"| Condition \\ {column_label} (reference: {reference}) | " + " | ".join(columns) + " |",
                "|" + "---|" * (len(columns) + 1)]
        for cond in conditions:
            out.append(f"| {cond} | " + " | ".join(_fmt_cell(cells[metric][cond][c]) for c in columns) + " |")
    return "\n".join(out) + "\n"


def _build(dataset: str, records: list[dict], header: dict) -> PublicResult:
    columns, conditions, cells = _aggregate(records)
    if dataset == "smartdoc_qa":
        reference = HUMAN
        md = _render(f"SmartDoc-QA Evaluation (reference: {HUMAN})",
                     "The reference text is the dataset's own human transcription, grouped by its three document classes. Not compared with results from other reference sources (ADR-0002).",
                     reference, "Document class", columns, conditions, cells, header)
    else:
        reference = PSEUDO_GT
        md = _render(f"RDD Evaluation (reference: {PSEUDO_GT})",
                     "RDD has no text: the reference is the OCR result of the lossless image of the same scene (pseudo ground truth). "
                     "CER reflects only the relative improvement, not true accuracy; not compared with results from other reference sources (ADR-0002).",
                     reference, "Scene", columns, conditions, cells, header)
    return PublicResult(dataset, reference, header, records, columns, conditions, cells, md)


DATASETS = {"smartdoc_qa": _smartdoc_records, "rdd": _rdd_records}


def run_public(root: Path, out_dir: Path,
               precomputed: Path | None = None) -> tuple[list[PublicResult], int, int]:
    """Score every public dataset found under `root`; returns (results, images OCR'd, images reused).
    The reports are written separately (see write_results)."""
    present = [name for name in DATASETS if (root / name).is_dir()]
    if not present:
        raise ReportError(f"no public dataset directory in {root} (expected {' / '.join(DATASETS)})")
    out_dir.mkdir(parents=True, exist_ok=True)
    ocr = OcrSource(precomputed, out_dir)
    results = []
    try:
        for name in present:
            results.append(_build(name, DATASETS[name](root / name, ocr), ocr.header))
    finally:  # keep finished OCR if a later dataset fails
        ocr.save()
    return results, ocr.n_ocr, ocr.n_cached


def write_results(results: list[PublicResult], out_dir: Path) -> None:
    for res in results:
        (out_dir / f"public_{res.dataset}.md").write_text(res.markdown, encoding="utf-8")
        (out_dir / f"public_{res.dataset}.json").write_text(json.dumps({
            "header": res.header, "reference": res.reference, "columns": res.columns,
            "conditions": res.conditions, "cells": res.cells, "records": res.records,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
