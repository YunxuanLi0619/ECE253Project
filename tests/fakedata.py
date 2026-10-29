"""Builders for a small fake capture dataset: hand-made CSV, tiny JPEGs, tiny text-layer PDF."""
import csv
from pathlib import Path

from PIL import Image

CSV_FIELDS = [
    "filename", "page_id", "doc_type", "condition", "seq", "phone_model", "light", "angle_deg",
    "blur_dir", "shadow_type", "split", "captured_at", "resolution", "pilot", "notes",
    "pdf_file", "pdf_page",
]
PROTOCOL = {"clean": 1, "blur": 3, "shadow": 3, "persp": 3, "combo": 2}

PROSE = [
    "Motion blur, shadows and perspective distortion are common defects",
    "in phone captured documents and they hurt optical character recognition",
    "accuracy far more than most people expect when they first measure it.",
]
# Each text line is (x, y, text). pdftotext reads TABLE row by row (as -layout does) but
# SCRAMBLED_TABLE column by column: its cells are tightly packed, short and many rows tall.
TABLE = [
    (x, 700 - 20 * r, f"{col}{r}")
    for r in range(8)
    for x, col in ((40, "alpha"), (200, "bravo"), (360, "charlie"), (520, "delta"))
]
SCRAMBLED_TABLE = [
    (x, 700 - 11 * r, f"{col} {r}")
    for r in range(30)
    for x, col in ((40, "left"), (120, "mid"), (200, "right"))
]


def _text_ops(lines: list[tuple[int, int, str]]) -> bytes:
    ops = [b"BT", b"/F1 10 Tf"]
    cx = cy = 0
    for x, y, s in lines:
        ops.append(f"{x - cx} {y - cy} Td".encode())
        ops.append(b"(" + s.replace("(", r"\(").replace(")", r"\)").encode("latin-1") + b") Tj")
        cx, cy = x, y
    ops.append(b"ET")
    return b"\n".join(ops)


def write_pdf(path: Path, pages: list[list[tuple[int, int, str]]]) -> None:
    """Minimal valid PDF, Helvetica, one content stream per page."""
    n = len(pages)
    objs: dict[int, bytes] = {1: b"<< /Type /Catalog /Pages 2 0 R >>"}
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode()
    font_id = 3 + 2 * n
    for i, lines in enumerate(pages):
        page_id, content_id = 3 + 2 * i, 4 + 2 * i
        objs[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_id} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        ).encode()
        stream = _text_ops(lines)
        objs[content_id] = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
    objs[font_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    out = bytearray(b"%PDF-1.4\n")
    offsets = {}
    for oid in sorted(objs):
        offsets[oid] = len(out)
        out += b"%d 0 obj\n" % oid + objs[oid] + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for oid in sorted(objs):
        out += b"%010d 00000 n \n" % offsets[oid]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(bytes(out))


def prose_page(offset: int = 0) -> list[tuple[int, int, str]]:
    return [(72, 700 - 16 * i, f"{line} {offset}") for i, line in enumerate(PROSE)]


class FakeDataset:
    """Pages p01..p04 (paper, book, table, receipt) all pointing at pages 1..4 of docs.pdf."""

    def __init__(self, root: Path, table=TABLE):
        self.root = root
        self.images = root / "images"
        self.pdfs = root / "pdf"
        self.csv = root / "meta.csv"
        self.images.mkdir()
        self.pdfs.mkdir()
        write_pdf(self.pdfs / "docs.pdf", [prose_page(1), prose_page(2), table, prose_page(4)])
        self.rows: list[dict] = []
        for i, doc_type in enumerate(["paper", "book", "table", "receipt"], start=1):
            for cond, count in PROTOCOL.items():
                for seq in range(1, count + 1):
                    self.add_image(i, doc_type, cond, seq, pdf_page=i)
        self.write()

    def add_image(self, page: int, doc_type: str, cond: str, seq: int, pdf_page: int,
                  filename: str | None = None, **overrides) -> None:
        name = filename or f"p{page:02d}_{cond}_{seq}.jpg"
        row = {f: "" for f in CSV_FIELDS}
        row.update(
            filename=name, page_id=f"p{page:02d}", doc_type=doc_type, condition=cond, seq=str(seq),
            phone_model="A" if page % 2 else "B", pilot="false",
            pdf_file="docs.pdf", pdf_page=str(pdf_page),
        )
        row.update(overrides)
        self.rows.append(row)
        Image.new("RGB", (8, 8), "white").save(self.images / name)

    def write(self) -> None:
        with open(self.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(self.rows)

    def drop_row(self, filename: str) -> None:
        """Remove the CSV row but leave the image on disk."""
        self.rows = [r for r in self.rows if r["filename"] != filename]
        self.write()

    def drop_image(self, filename: str) -> None:
        """Delete the image file but leave the CSV row."""
        (self.images / filename).unlink()


TYPE_COUNTS_36 = {"paper": 12, "book": 10, "table": 8, "receipt": 6}


def write_page_csv(path: Path, type_counts: dict[str, int] = TYPE_COUNTS_36, rows_per_page: int = 3,
                   pilot_pages: tuple[int, ...] = (), phone_of=lambda page: "A" if page % 2 else "B") -> None:
    """Metadata CSV only (no images, no PDFs): enough for tools that work on pages, like the split."""
    page = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for doc_type, n in type_counts.items():
            for _ in range(n):
                page += 1
                for seq in range(1, rows_per_page + 1):
                    row = {k: "" for k in CSV_FIELDS}
                    row.update(
                        filename=f"p{page:02d}_blur_{seq}.jpg", page_id=f"p{page:02d}", doc_type=doc_type,
                        condition="blur", seq=str(seq), phone_model=phone_of(page), notes=f"keep-{page}",
                        pilot="true" if page in pilot_pages else "false",
                        pdf_file="docs.pdf", pdf_page="1",
                    )
                    w.writerow(row)


class Capture:
    """A fake capture for the baseline report: pages with chosen images, and the per-image CER that a
    precomputed-OCR file hands to the CLI (so no Tesseract is needed). WER is set equal to CER."""

    def __init__(self, root: Path):
        self.root = root
        self.images = root / "images"
        self.pdfs = root / "pdf"
        self.csv = root / "meta.csv"
        self.out = root / "out"
        self.precomputed = root / "precomputed.json"
        self.images.mkdir()
        self.pdfs.mkdir()
        write_pdf(self.pdfs / "docs.pdf", [prose_page(1)])
        self.rows: list[dict] = []
        self.cers: dict[str, float] = {}

    def add_page(self, page: int, doc_type: str, shots: dict[str, list[float]], pilot: bool = False) -> None:
        """shots: condition -> CER of each image of that condition, in seq order."""
        for cond, values in shots.items():
            for seq, cer in enumerate(values, start=1):
                name = f"p{page:02d}_{cond}_{seq}.jpg"
                row = {f: "" for f in CSV_FIELDS}
                row.update(filename=name, page_id=f"p{page:02d}", doc_type=doc_type, condition=cond,
                           seq=str(seq), phone_model="A", pilot="true" if pilot else "false",
                           pdf_file="docs.pdf", pdf_page="1")
                self.rows.append(row)
                self.cers[name] = cer
                Image.new("RGB", (8, 8), "white").save(self.images / name)

    def write(self) -> None:
        import json
        with open(self.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(self.rows)
        self.precomputed.write_text(
            json.dumps({n: {"cer": c, "wer": c} for n, c in self.cers.items()}), encoding="utf-8")

    def argv(self, *extra: str, precomputed: bool = True) -> list[str]:
        self.write()
        return ["report", "--csv", str(self.csv), "--images", str(self.images), "--pdfs", str(self.pdfs),
                "--out", str(self.out), *(["--precomputed", str(self.precomputed)] if precomputed else []), *extra]

    def summary(self) -> dict:
        import json
        return json.loads((self.out / "baseline_summary.json").read_text(encoding="utf-8"))


SD_CLASSES = ("modern documents", "old administrative letters", "receipts")


class FakePublic:
    """A small fake public-dataset directory for the `public` mode.

    <root>/smartdoc_qa/{manifest.csv, images/, transcriptions/}  (human transcription)
    <root>/rdd/{manifest.csv, images/}                            (no text: pseudo ground truth)
    The raw OCR text of every image is handed to the CLI as a precomputed JSON, so no Tesseract is needed."""

    def __init__(self, root: Path):
        self.root = root / "public"
        self.out = root / "out"
        self.ocr_texts = root / "ocr_texts.json"
        self.sd_rows: list[dict] = []
        self.rdd_rows: list[dict] = []
        self.texts: dict[str, str] = {}
        self.transcriptions: dict[str, str] = {}

    def add_smartdoc(self, filename: str, page_id: str, doc_class: str, distortion: str,
                     reference: str, ocr: str) -> None:
        ref_file = f"{page_id}.txt"
        self.transcriptions[ref_file] = reference
        self.sd_rows.append({"filename": filename, "page_id": page_id, "doc_class": doc_class,
                             "distortion": distortion, "reference": ref_file})
        self.texts[f"smartdoc_qa/{filename}"] = ocr

    def add_rdd(self, filename: str, page_id: str, condition: str, ocr: str) -> None:
        self.rdd_rows.append({"filename": filename, "page_id": page_id, "condition": condition})
        self.texts[f"rdd/{filename}"] = ocr

    def _dataset(self, name: str, rows: list[dict]) -> Path:
        d = self.root / name
        (d / "images").mkdir(parents=True, exist_ok=True)
        for r in rows:
            Image.new("RGB", (8, 8), "white").save(d / "images" / r["filename"])
        with open(d / "manifest.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        return d

    def write(self) -> None:
        import json
        if self.sd_rows:
            d = self._dataset("smartdoc_qa", self.sd_rows)
            (d / "transcriptions").mkdir(exist_ok=True)
            for name, text in self.transcriptions.items():
                (d / "transcriptions" / name).write_text(text, encoding="utf-8")
        if self.rdd_rows:
            self._dataset("rdd", self.rdd_rows)
        self.ocr_texts.write_text(json.dumps(self.texts), encoding="utf-8")

    def argv(self, *extra: str, precomputed: bool = True) -> list[str]:
        self.write()
        return ["public", "--root", str(self.root), "--out", str(self.out),
                *(["--ocr-texts", str(self.ocr_texts)] if precomputed else []), *extra]

    def summary(self, dataset: str) -> dict:
        import json
        return json.loads((self.out / f"public_{dataset}.json").read_text(encoding="utf-8"))

    def report(self, dataset: str) -> str:
        return (self.out / f"public_{dataset}.md").read_text(encoding="utf-8")
