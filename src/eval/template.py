"""Metadata CSV skeleton and shot list for a page list: the planning side of the capture protocol.

The page list holds one row per page (page_id, doc_type, pdf_file, pdf_page; optional phone_model and
pilot). Each page expands to the 12 protocol shots with the protocol's fields prefilled; what is only
known while shooting (light, captured_at, resolution, notes) and the split stay empty."""
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .dataset import CONDITIONS, CSV_FIELDS, DOC_TYPES, PER_PAGE_COUNTS, _is_pilot, page_label, read_rows

REQUIRED_COLUMNS = ("page_id", "doc_type", "pdf_file", "pdf_page")
BLUR_DIRS = ("horizontal", "vertical", "diagonal")
PERSP_ANGLES = ("15", "30", "45")
COMBO_SHADOWS = ("hard", "soft")
SHOT_HINTS = {
    "clean": "Clean baseline: flat, phone on a stand shooting straight down, same room ceiling light, dark tablecloth",
    "blur": {"horizontal": "Blur: horizontal translation", "vertical": "Blur: vertical hand shake", "diagonal": "Blur: diagonal, shooting while walking"},
    "shadow": "Shadow (type not specified by the protocol, record it in shadow_type while shooting)",
    "persp": "Perspective: tilt {angle}° (±5°), protractor template on the desk",
    "combo": "Combo: tilt, {shadow} shadow and motion blur at the same time",
}


class TemplateError(Exception):
    pass


@dataclass
class Template:
    rows: list[dict]
    checklist: str
    warnings: list[str]


def _read_pages(pages_csv: Path) -> list[dict]:
    columns, rows = read_rows(pages_csv)
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise TemplateError(f"page list is missing column(s): {', '.join(missing)}")
    errors, pages, first_line = [], [], {}
    for line, row in enumerate(rows, start=2):
        label = page_label(row["page_id"])
        if label is None:
            errors.append(f"line {line}: bad page_id '{row['page_id']}'")
            continue
        doc_type = row["doc_type"].strip()
        if doc_type not in DOC_TYPES:
            errors.append(f"line {line} (page {label}): unknown doc_type '{doc_type}', "
                          f"expected one of {', '.join(DOC_TYPES)}")
        if not row["pdf_file"].strip():
            errors.append(f"line {line} (page {label}): pdf_file is empty")
        pdf_page = row["pdf_page"].strip()
        if not (pdf_page.isdigit() and int(pdf_page) >= 1):
            errors.append(f"line {line} (page {label}): pdf_page '{pdf_page}' must be a positive integer")
        if label in first_line:
            errors.append(f"line {line}: duplicate page {label} (first on line {first_line[label]})")
        first_line.setdefault(label, line)
        pages.append({"label": label, "doc_type": doc_type, "pdf_file": row["pdf_file"].strip(),
                      "pdf_page": pdf_page, "phone": (row.get("phone_model") or "").strip(),
                      "pilot": _is_pilot(row.get("pilot") or "")})
    if errors:
        raise TemplateError("\n".join(errors))
    return pages


def _shots(cond: str):
    """(seq, blur_dir, angle_deg, shadow_type, hint) for each shot of a condition."""
    for seq in range(1, PER_PAGE_COUNTS[cond] + 1):
        blur_dir = BLUR_DIRS[seq - 1] if cond == "blur" else ""
        angle = PERSP_ANGLES[seq - 1] if cond == "persp" else ""
        shadow = COMBO_SHADOWS[seq - 1] if cond == "combo" else ""
        hint = SHOT_HINTS[cond]
        if cond == "blur":
            hint = hint[blur_dir]
        elif cond in ("persp", "combo"):
            hint = hint.format(angle=angle, shadow="hard" if shadow == "hard" else "soft")
        yield seq, blur_dir, angle, shadow, hint


def build_template(pages_csv: Path) -> Template:
    pages = _read_pages(pages_csv)
    rows, warnings, lines = [], [], ["# Shot List", ""]
    phones: dict[str, Counter] = {}
    for page in pages:
        label = page["label"]
        phone = page["phone"] or ("A" if int(label[1:]) % 2 else "B")
        phones.setdefault(page["doc_type"], Counter())[phone] += 1
        tag = " · pilot" if page["pilot"] else ""
        lines += [f"## {label} · {page['doc_type']} · phone {phone} · "
                  f"{page['pdf_file']} page {page['pdf_page']}{tag}", ""]
        for cond in CONDITIONS:
            for seq, blur_dir, angle, shadow, hint in _shots(cond):
                filename = f"{label}_{cond}_{seq}.jpg"
                row = {f: "" for f in CSV_FIELDS}
                row.update(filename=filename, page_id=label, doc_type=page["doc_type"], condition=cond,
                           seq=str(seq), phone_model=phone, blur_dir=blur_dir, angle_deg=angle,
                           shadow_type=shadow, pilot="true" if page["pilot"] else "false",
                           pdf_file=page["pdf_file"], pdf_page=page["pdf_page"])
                rows.append(row)
                lines.append(f"- [ ] {filename} — {hint}")
        lines.append("")
    for doc_type, counts in phones.items():
        if max(counts.values()) - min(counts.get(p, 0) for p in "AB") > 1:
            warnings.append(f"WARNING: phones are lopsided within {doc_type}: "
                            f"A {counts['A']}, B {counts['B']} (odd pages A, even pages B)")
    return Template(rows, "\n".join(lines), warnings)


def write_template(tpl: Template, csv_path: Path, checklist_path: Path) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(tpl.rows)
    checklist_path.write_text(tpl.checklist, encoding="utf-8")
