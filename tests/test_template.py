"""CSV skeleton + shot list from a page list, through the CLI entry point."""
import csv
import re
from collections import Counter

import pytest
from PIL import Image

from eval.cli import main
from fakedata import TYPE_COUNTS_36, prose_page, write_pdf

PAGE_FIELDS = ["page_id", "doc_type", "pdf_file", "pdf_page", "phone_model", "pilot"]


def write_pages(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PAGE_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in PAGE_FIELDS})


def pages_36(overrides: dict | None = None) -> list[dict]:
    """p01..p36: paper 1-12, book 13-22, table 23-30, receipt 31-36, each one page of docs.pdf."""
    rows, page = [], 0
    for doc_type, n in TYPE_COUNTS_36.items():
        for _ in range(n):
            page += 1
            rows.append({"page_id": f"p{page:02d}", "doc_type": doc_type, "pdf_file": "docs.pdf",
                         "pdf_page": str(page), **(overrides or {}).get(page, {})})
    return rows


class Setup:
    def __init__(self, root, rows=None):
        self.root = root
        self.pages = root / "pages.csv"
        self.csv = root / "meta.csv"
        self.checklist = root / "shotlist.md"
        write_pages(self.pages, rows if rows is not None else pages_36())

    def argv(self):
        return ["template", "--pages", str(self.pages), "--csv", str(self.csv),
                "--checklist", str(self.checklist)]

    def rows(self) -> list[dict]:
        with open(self.csv, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


@pytest.fixture
def setup(tmp_path):
    return Setup(tmp_path)


def test_36_pages_give_432_rows_with_twelve_per_page(setup):
    assert main(setup.argv()) == 0
    rows = setup.rows()
    assert len(rows) == 432
    assert all(re.fullmatch(r"p\d{2}_(clean|blur|shadow|persp|combo)_\d\.jpg", r["filename"]) for r in rows)
    per_page = Counter(r["page_id"] for r in rows)
    assert set(per_page.values()) == {12} and len(per_page) == 36
    p7 = Counter(r["condition"] for r in rows if r["page_id"] == "p07")
    assert p7 == {"clean": 1, "blur": 3, "shadow": 3, "persp": 3, "combo": 2}
    first = rows[0]
    assert (first["page_id"], first["doc_type"], first["pdf_file"], first["pdf_page"]) == ("p01", "paper", "docs.pdf", "1")
    assert first["split"] == "" and first["captured_at"] == ""  # filled in later, never by the template


def test_protocol_fields_are_prefilled(setup):
    assert main(setup.argv()) == 0
    p1 = {r["filename"]: r for r in setup.rows() if r["page_id"] == "p01"}
    assert [p1[f"p01_blur_{i}.jpg"]["blur_dir"] for i in (1, 2, 3)] == ["horizontal", "vertical", "diagonal"]
    assert [p1[f"p01_persp_{i}.jpg"]["angle_deg"] for i in (1, 2, 3)] == ["15", "30", "45"]
    assert [p1[f"p01_combo_{i}.jpg"]["shadow_type"] for i in (1, 2)] == ["hard", "soft"]
    # the protocol does not fix a shadow type for the plain shadow condition, so it is left to the shoot
    assert all(p1[f"p01_shadow_{i}.jpg"]["shadow_type"] == "" for i in (1, 2, 3))
    assert p1["p01_clean_1.jpg"]["blur_dir"] == p1["p01_clean_1.jpg"]["angle_deg"] == ""


def test_phones_split_odd_even_and_balance_within_each_type(setup, capsys):
    assert main(setup.argv()) == 0
    by_page = {r["page_id"]: r["phone_model"] for r in setup.rows()}
    assert by_page["p01"] == "A" and by_page["p02"] == "B" and by_page["p03"] == "A"
    types = {r["page_id"]: r["doc_type"] for r in setup.rows()}
    for doc_type in TYPE_COUNTS_36:
        phones = Counter(by_page[p] for p, t in types.items() if t == doc_type)
        assert phones["A"] == phones["B"], doc_type
    assert "WARNING" not in capsys.readouterr().out


def test_lopsided_phone_split_in_a_type_is_warned_about(tmp_path, capsys):
    rows = [{"page_id": f"p{n:02d}", "doc_type": "paper", "pdf_file": "docs.pdf", "pdf_page": "1"}
            for n in (1, 3, 5, 7)]  # all odd pages: phone A only
    s = Setup(tmp_path, rows)
    assert main(s.argv()) == 0
    assert "WARNING" in capsys.readouterr().out


def test_phone_given_in_the_page_list_wins(tmp_path):
    s = Setup(tmp_path, pages_36({1: {"phone_model": "B"}}))
    assert main(s.argv()) == 0
    assert {r["phone_model"] for r in s.rows() if r["page_id"] == "p01"} == {"B"}


def test_checklist_is_grouped_by_page_with_checkboxes_and_marks_pilot_pages(tmp_path):
    s = Setup(tmp_path, pages_36({2: {"pilot": "true"}}))
    assert main(s.argv()) == 0
    text = s.checklist.read_text(encoding="utf-8")
    assert len(re.findall(r"^- \[ \] ", text, flags=re.M)) == 432
    assert "- [ ] p07_blur_2.jpg" in text and "- [ ] p07_persp_3.jpg" in text
    headings = {m.group(1): m.group(0) for m in re.finditer(r"^#+ .*?(p\d{2}).*$", text, flags=re.M)}
    assert "试拍" in headings["p02"] and "试拍" not in headings["p01"]
    assert {r["pilot"] for r in s.rows() if r["page_id"] == "p02"} == {"true"}
    assert {r["pilot"] for r in s.rows() if r["page_id"] == "p01"} == {"false"}


def test_existing_output_is_never_overwritten(setup, capsys):
    setup.csv.write_text("precious", encoding="utf-8")
    assert main(setup.argv()) == 1
    assert "meta.csv" in capsys.readouterr().out
    assert setup.csv.read_text(encoding="utf-8") == "precious"
    assert not setup.checklist.exists()  # nothing half-written

    setup.csv.unlink()
    setup.checklist.write_text("mine", encoding="utf-8")
    assert main(setup.argv()) == 1
    assert "shotlist.md" in capsys.readouterr().out
    assert not setup.csv.exists()


@pytest.mark.parametrize("edit, culprit", [
    ({"doc_type": "poster"}, "poster"),
    ({"pdf_page": ""}, "pdf_page"),
    ({"pdf_page": "0"}, "pdf_page"),
    ({"pdf_file": ""}, "pdf_file"),
    ({"page_id": "page-one"}, "page-one"),
])
def test_bad_page_list_rows_are_named_and_nothing_is_written(tmp_path, capsys, edit, culprit):
    rows = pages_36()
    rows[4] = {**rows[4], **edit}  # CSV line 6
    s = Setup(tmp_path, rows)
    assert main(s.argv()) == 1
    out = capsys.readouterr().out
    assert "line 6" in out and culprit in out
    assert not s.csv.exists() and not s.checklist.exists()


def test_duplicate_page_in_page_list_is_rejected(tmp_path, capsys):
    rows = pages_36()
    rows[1] = {**rows[1], "page_id": "p01"}
    s = Setup(tmp_path, rows)
    assert main(s.argv()) == 1
    out = capsys.readouterr().out
    assert "p01" in out and "duplicate" in out
    assert not s.csv.exists()


def test_page_list_missing_a_required_column_is_reported(tmp_path, capsys):
    s = Setup(tmp_path)
    s.pages.write_text("page_id,doc_type\np01,paper\n", encoding="utf-8")
    assert main(s.argv()) == 1
    assert "pdf_file" in capsys.readouterr().out


def test_skeleton_passes_validate_once_the_photos_exist(tmp_path):
    s = Setup(tmp_path)
    assert main(s.argv()) == 0
    images, pdfs = tmp_path / "images", tmp_path / "pdf"
    images.mkdir()
    pdfs.mkdir()
    write_pdf(pdfs / "docs.pdf", [prose_page(i) for i in range(1, 37)])
    for r in s.rows():
        Image.new("RGB", (8, 8), "white").save(images / r["filename"])
    assert main(["validate", "--csv", str(s.csv), "--images", str(images), "--pdfs", str(pdfs)]) == 0
