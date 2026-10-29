"""Dataset validation, exercised only through the CLI entry point on a small fake dataset."""
import pytest

from eval.cli import main
from fakedata import SCRAMBLED_TABLE, FakeDataset, write_pdf


@pytest.fixture
def ds(tmp_path):
    return FakeDataset(tmp_path)


def validate(ds, capsys, *extra):
    code = main(["validate", "--csv", str(ds.csv), "--images", str(ds.images),
                 "--pdfs", str(ds.pdfs), *extra])
    out = capsys.readouterr().out
    return code, out


def lines(out, level):
    return [l for l in out.splitlines() if l.startswith(level)]


def test_valid_dataset_passes(ds, capsys):
    code, out = validate(ds, capsys)
    assert code == 0, out
    assert not lines(out, "ERROR") and not lines(out, "WARNING")
    assert "OK" in out


def test_misnamed_file_names_the_file(ds, capsys):
    ds.rows[0]["filename"] = "page1-clean.jpg"
    ds.write()
    (ds.images / "p01_clean_1.jpg").rename(ds.images / "page1-clean.jpg")
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("page1-clean.jpg" in l and "p<page>_<condition>_<seq>.jpg" in l for l in lines(out, "ERROR"))


def test_unknown_condition_names_the_file(ds, capsys):
    ds.rows[1]["filename"] = "p01_sharp_1.jpg"
    ds.rows[1]["condition"] = "sharp"
    ds.write()
    (ds.images / "p01_blur_1.jpg").rename(ds.images / "p01_sharp_1.jpg")
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p01_sharp_1.jpg" in l and "sharp" in l and "clean" in l for l in lines(out, "ERROR"))


def test_image_without_csv_row_is_reported(ds, capsys):
    ds.drop_row("p02_blur_3.jpg")
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p02_blur_3.jpg" in l and "no CSV row" in l for l in lines(out, "ERROR"))


def test_csv_row_without_image_is_reported(ds, capsys):
    ds.drop_image("p03_shadow_2.jpg")
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p03_shadow_2.jpg" in l and "image file missing" in l and "line" in l
               for l in lines(out, "ERROR"))


def test_orphan_image_is_reported(ds, capsys):
    (ds.images / "p01_clean_1.jpg").rename(ds.images / "p09_clean_1.jpg")
    ds.write()
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p09_clean_1.jpg" in l and "no CSV row" in l for l in lines(out, "ERROR"))


def test_wrong_count_per_page_names_page_and_condition(ds, capsys):
    ds.rows = [r for r in ds.rows if r["filename"] != "p04_persp_3.jpg"]
    ds.write()
    (ds.images / "p04_persp_3.jpg").unlink()
    ds.add_image(4, "receipt", "blur", 4, pdf_page=4)
    ds.write()
    code, out = validate(ds, capsys)
    errs = lines(out, "ERROR")
    assert code == 1
    assert any("p04" in l and "persp" in l and "2" in l and "expected 3" in l for l in errs)
    assert any("p04" in l and "blur" in l and "4" in l and "expected 3" in l for l in errs)


def test_page_without_a_condition_reports_zero(ds, capsys):
    for r in [r for r in ds.rows if r["page_id"] == "p02" and r["condition"] == "combo"]:
        ds.drop_row(r["filename"])
        ds.drop_image(r["filename"])
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p02" in l and "combo" in l and "0" in l and "expected 2" in l
               for l in lines(out, "ERROR"))


def test_csv_fields_must_agree_with_filename(ds, capsys):
    ds.rows[0]["condition"] = "blur"
    ds.write()
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p01_clean_1.jpg" in l and "condition" in l for l in lines(out, "ERROR"))


def test_missing_csv_column_is_reported(ds, capsys):
    text = ds.csv.read_text(encoding="utf-8").replace("pdf_page", "pdf_pg")
    ds.csv.write_text(text, encoding="utf-8")
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("pdf_page" in l and "column" in l for l in lines(out, "ERROR"))


def test_page_pointing_past_end_of_pdf_is_an_error(ds, capsys):
    for r in ds.rows:
        if r["page_id"] == "p01":
            r["pdf_page"] = "9"
    ds.write()
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p01" in l and "ground truth" in l for l in lines(out, "ERROR"))


def test_page_with_missing_pdf_is_an_error(ds, capsys):
    for r in ds.rows:
        if r["page_id"] == "p01":
            r["pdf_file"] = "nope.pdf"
    ds.write()
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p01" in l and "nope.pdf" in l for l in lines(out, "ERROR"))


def test_page_without_pdf_link_is_an_error(ds, capsys):
    for r in ds.rows:
        if r["page_id"] == "p01":
            r["pdf_file"] = ""
    ds.write()
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p01" in l and "pdf_file" in l for l in lines(out, "ERROR"))


def test_rows_of_one_page_must_share_the_pdf_link(ds, capsys):
    ds.rows[0]["pdf_page"] = "2"
    ds.write()
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p01" in l and "disagree" in l for l in lines(out, "ERROR"))


def test_empty_text_layer_warns_but_passes(ds, capsys):
    write_pdf(ds.pdfs / "docs.pdf", [[(72, 700, "")], [(72, 700, "x")], [(72, 700, "y")], [(72, 700, "z")]])
    code, out = validate(ds, capsys)
    assert code == 0
    warns = lines(out, "WARNING")
    assert any("p01" in l and "empty" in l for l in warns)


def test_short_text_layer_warns_and_threshold_is_adjustable(ds, capsys):
    write_pdf(ds.pdfs / "docs.pdf", [[(72, 700, "tiny page")]] * 4)
    code, out = validate(ds, capsys)
    assert code == 0
    assert any("p01" in l and "short" in l for l in lines(out, "WARNING"))
    code, out = validate(ds, capsys, "--min-chars", "5")
    assert not lines(out, "WARNING")


def test_scrambled_table_reading_order_warns(tmp_path, capsys):
    ds = FakeDataset(tmp_path, table=SCRAMBLED_TABLE)
    code, out = validate(ds, capsys)
    assert code == 0
    warns = lines(out, "WARNING")
    assert any("p03" in l and "reading order" in l for l in warns)
    assert not any("p01" in l or "p02" in l or "p04" in l for l in warns)


def test_well_ordered_table_does_not_warn(ds, capsys):
    code, out = validate(ds, capsys)
    assert not any("p03" in l for l in lines(out, "WARNING"))


def test_unknown_doc_type_is_an_error(ds, capsys):
    for r in ds.rows:
        if r["page_id"] == "p04":
            r["doc_type"] = "recipt"
    ds.write()
    code, out = validate(ds, capsys)
    assert code == 1
    assert any("p04" in l and "recipt" in l for l in lines(out, "ERROR"))


def test_unreadable_csv_exits_2(ds, capsys):
    ds.csv.unlink()
    code, out = validate(ds, capsys)
    assert code == 2
