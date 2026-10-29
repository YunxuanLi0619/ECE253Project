"""P0 baseline run: fixed-config OCR on every image, per-image CER/WER kept as the raw data.

Results live in one JSON file whose header records the tesseract version, PSM/OEM and normalization
version (ADR-0001). An image is OCR'd again only when it is new, its bytes changed, its ground truth
changed, or the header changed."""
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from .dataset import page_label, read_rows
from .groundtruth import pdf_ground_truth
from .metrics import score
from .normalize import NORMALIZE_VERSION, normalize
from .ocr import OCR_CONFIG, ocr_image, tesseract_version

RESULTS_FILE = "p0_results.json"


class ReportError(Exception):
    """The baseline cannot be run; the message names the offending file, row or page."""


@dataclass
class Baseline:
    header: dict
    records: list[dict]  # one per CSV row: metadata + scores
    n_ocr: int  # images OCR'd in this run
    n_cached: int  # images whose stored result was reused


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _page_ground_truths(rows: list[dict], pdf_dir: Path) -> dict[str, str]:
    """Normalized ground truth per page label, from each page's source PDF."""
    gts: dict[str, str] = {}
    for line, row in enumerate(rows, start=2):
        label = page_label(row["page_id"])
        if label is None:
            raise ReportError(f"CSV line {line} ({row['filename']}): bad page_id '{row['page_id']}'")
        if label in gts:
            continue
        pdf, page = row["pdf_file"].strip(), row["pdf_page"].strip()
        if not pdf or not page.isdigit() or int(page) < 1:
            raise ReportError(
                f"page {label} (CSV line {line}): needs pdf_file and a 1-based pdf_page, got '{pdf}' / '{page}'")
        if not (pdf_dir / pdf).is_file():
            raise ReportError(f"page {label}: source PDF {pdf} not found in {pdf_dir}")
        text = normalize(pdf_ground_truth(pdf_dir / pdf, int(page)))
        if not text:
            raise ReportError(f"page {label}: text layer is empty ({pdf} p.{page}), no ground truth")
        gts[label] = text
    return gts


def _ocr_upright(path: Path) -> str:
    """OCR one photo, turned upright by its EXIF orientation tag (Tesseract ignores the tag).

    The file on disk is never modified; a turned copy is written as PNG only when the tag asks for it."""
    with Image.open(path) as img:
        if img.getexif().get(0x0112, 1) == 1:
            return ocr_image(path)
        upright = ImageOps.exif_transpose(img)
    with tempfile.TemporaryDirectory() as tmp:
        turned = Path(tmp) / "upright.png"
        upright.save(turned)
        return ocr_image(turned)


def _load_precomputed(path: Path, rows: list[dict]) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [r["filename"] for r in rows if r["filename"] not in data]
    if missing:
        raise ReportError(f"precomputed results {path} lack {len(missing)} image(s): {', '.join(missing)}")
    return data


def _load_cache(path: Path, header: dict) -> dict[str, dict]:
    if not path.is_file():
        return {}
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
        return stored["images"] if stored["header"] == header else {}
    except (ValueError, KeyError, TypeError):
        return {}


def _save_json(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def _save(path: Path, header: dict, images: dict[str, dict]) -> None:
    _save_json(path, {"header": header, "images": images})


def run_baseline(csv_path: Path, images_dir: Path, pdf_dir: Path, out_dir: Path,
                 precomputed: Path | None = None) -> Baseline:
    """Score every image of the CSV against its page's ground truth, reusing stored results.

    With `precomputed` (a JSON of filename -> {cer, wer}) no OCR runs and no result file is written."""
    _, rows = read_rows(csv_path)
    if not rows:
        raise ReportError(f"{csv_path} has no rows")
    missing = [r["filename"] for r in rows if not (images_dir / r["filename"]).is_file()]
    if missing:
        raise ReportError(f"image file(s) missing from {images_dir}: {', '.join(missing)}")
    gts = _page_ground_truths(rows, pdf_dir)

    if precomputed is not None:
        header = {"ocr": f"precomputed from {precomputed.name}", "normalize_version": NORMALIZE_VERSION}
        given = _load_precomputed(precomputed, rows)
        stored = {}
        for r in rows:
            n_chars = len(gts[page_label(r["page_id"])])
            n_words = len(gts[page_label(r["page_id"])].split())
            stored[r["filename"]] = {
                "cer": given[r["filename"]]["cer"], "wer": given[r["filename"]]["wer"],
                "char_N": n_chars, "word_N": n_words}
        return Baseline(header, _records(rows, stored), 0, 0)

    out_dir.mkdir(parents=True, exist_ok=True)
    header = {"tesseract": tesseract_version(), "ocr_config": OCR_CONFIG,
              "normalize_version": NORMALIZE_VERSION}
    path = out_dir / RESULTS_FILE
    stored = _load_cache(path, header)
    fresh: dict[str, dict] = {}
    n_ocr = n_cached = 0
    try:
        for r in rows:
            name = r["filename"]
            gt = gts[page_label(r["page_id"])]
            sha, gt_sha = _sha256((images_dir / name).read_bytes()), _sha256(gt.encode("utf-8"))
            entry = stored.get(name)
            if entry and entry["sha256"] == sha and entry["gt_sha256"] == gt_sha:
                n_cached += 1
            else:
                entry = {"sha256": sha, "gt_sha256": gt_sha,
                         **score(gt, normalize(_ocr_upright(images_dir / name))).to_dict()}
                n_ocr += 1
            fresh[name] = entry
    finally:  # keep finished work if OCR dies halfway
        _save(path, header, {**stored, **fresh} if len(fresh) < len(rows) else fresh)
    return Baseline(header, _records(rows, fresh), n_ocr, n_cached)


def _records(rows: list[dict], scores: dict[str, dict]) -> list[dict]:
    return [{
        "filename": r["filename"], "page_id": page_label(r["page_id"]), "doc_type": r["doc_type"].strip(),
        "condition": r["condition"].strip(), "pilot": r["pilot"].strip().lower() in {"true", "1", "yes"},
        "cer": scores[r["filename"]]["cer"], "wer": scores[r["filename"]]["wer"],
        "char_N": scores[r["filename"]]["char_N"], "word_N": scores[r["filename"]]["word_N"],
    } for r in rows]
