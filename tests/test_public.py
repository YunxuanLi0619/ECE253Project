"""Public-dataset tables through the CLI entry point: one table per reference source (ADR-0002)."""
import json
import os
import shutil
from pathlib import Path

import pytest
from PIL import Image

from eval.cli import main
from fakedata import SD_CLASSES, FakePublic

REF = "alpha bravo charlie delta"  # 25 characters, 4 words
ONE_WRONG = "alpha bravo charlie delto"  # 1 substitution: CER 0.04


@pytest.fixture
def pub(tmp_path):
    return FakePublic(tmp_path)


def run(pub, *extra) -> None:
    assert main(pub.argv(*extra)) == 0


def cell(summary, cond, col, metric="cer"):
    return summary["cells"][metric][cond][col]


def fill_smartdoc(pub):
    for i, cls in enumerate(SD_CLASSES, start=1):
        pub.add_smartdoc(f"s{i}_blur_1.jpg", f"s{i}", cls, "blur", REF, ONE_WRONG)
        pub.add_smartdoc(f"s{i}_light_1.jpg", f"s{i}", cls, "light", REF, REF)


def fill_rdd(pub):
    pub.add_rdd("r1_clean.jpg", "r1", "clean", REF)
    pub.add_rdd("r1_shadow.jpg", "r1", "shadow", ONE_WRONG)


def test_smartdoc_table_is_grouped_by_its_three_document_classes(pub):
    fill_smartdoc(pub)
    run(pub)
    s = pub.summary("smartdoc_qa")
    assert s["columns"] == list(SD_CLASSES)
    for cls in SD_CLASSES:
        assert cell(s, "blur", cls)["mean"] == pytest.approx(0.04)
        assert cell(s, "blur", cls)["n"] == 1
        assert cell(s, "light", cls)["mean"] == 0.0
    md = pub.report("smartdoc_qa")
    assert all(cls in md for cls in SD_CLASSES)


def test_smartdoc_header_says_human_transcription(pub):
    fill_smartdoc(pub)
    run(pub)
    md = pub.report("smartdoc_qa")
    table_header = next(line for line in md.splitlines() if line.startswith("| ") and "Condition" in line)
    assert "human transcription" in table_header
    assert "human transcription" in md.split("\n")[0]


def test_rdd_header_says_pseudo_ground_truth_relative_only(pub):
    fill_rdd(pub)
    run(pub)
    md = pub.report("rdd")
    table_header = next(line for line in md.splitlines() if line.startswith("| ") and "Condition" in line)
    assert "pseudo ground truth, relative improvement only" in table_header
    assert "pseudo ground truth, relative improvement only" in md.split("\n")[0]


def test_rdd_scores_shadow_images_against_ocr_of_the_clean_image_of_the_scene(pub):
    # the reference is the OCR text of the clean image (not a transcription); the clean image itself is not scored
    pub.add_rdd("r1_clean.jpg", "r1", "clean", "alpha bravo charlie delta")
    pub.add_rdd("r1_shadow.jpg", "r1", "shadow", "alpha bravo")
    pub.add_rdd("r2_clean.jpg", "r2", "clean", "one two")
    pub.add_rdd("r2_shadow.jpg", "r2", "shadow", "one two")
    run(pub)
    s = pub.summary("rdd")
    assert s["conditions"] == ["shadow"]
    c = cell(s, "shadow", "all")
    assert c["n"] == 2
    # r1: 14 of 25 characters missing = 0.56; r2: 0
    assert c["mean"] == pytest.approx(0.28)
    assert [r["filename"] for r in s["records"]] == ["r1_shadow.jpg", "r2_shadow.jpg"]


def test_reference_sources_never_share_a_table_or_file(pub):
    fill_smartdoc(pub)
    fill_rdd(pub)
    run(pub)
    sd, rdd = pub.report("smartdoc_qa"), pub.report("rdd")
    assert "pseudo ground truth" not in sd and "RDD" not in sd
    assert "human transcription" not in rdd and "SmartDoc" not in rdd
    assert not any(cls in rdd for cls in SD_CLASSES)
    assert [p.name for p in sorted(pub.out.glob("public_*.md"))] == ["public_rdd.md", "public_smartdoc_qa.md"]


def test_only_present_datasets_get_a_table(pub):
    fill_rdd(pub)
    run(pub)
    assert not (pub.out / "public_smartdoc_qa.md").exists()
    assert (pub.out / "public_rdd.md").exists()


def test_all_references_go_through_the_shared_normalization(pub):
    # transcription with line breaks / double spaces, OCR with different whitespace: still a perfect match
    pub.add_smartdoc("s1_blur_1.jpg", "s1", SD_CLASSES[0], "blur", "alpha  bravo\ncharlie\n\ndelta ", "alpha bravo\n charlie delta")
    pub.add_rdd("r1_clean.jpg", "r1", "clean", "alpha  bravo\ncharlie delta")
    pub.add_rdd("r1_shadow.jpg", "r1", "shadow", "alpha bravo charlie\n\ndelta")
    run(pub)
    assert cell(pub.summary("smartdoc_qa"), "blur", SD_CLASSES[0])["mean"] == 0.0
    assert cell(pub.summary("rdd"), "shadow", "all")["mean"] == 0.0


def test_cells_are_page_level_means_with_n_and_median(pub):
    # page s1: two blur shots 0.0 and 0.08 -> page mean 0.04; page s2: 0.2 -> macro 0.12
    pub.add_smartdoc("s1_blur_1.jpg", "s1", SD_CLASSES[0], "blur", REF, REF)
    pub.add_smartdoc("s1_blur_2.jpg", "s1", SD_CLASSES[0], "blur", REF, "alpha bravo charlie dxlto")
    pub.add_smartdoc("s2_blur_1.jpg", "s2", SD_CLASSES[0], "blur", REF, "alpha bravo charl1e dxlt1")
    run(pub)
    c = cell(pub.summary("smartdoc_qa"), "blur", SD_CLASSES[0])
    assert c["n"] == 2
    assert c["mean"] == pytest.approx((0.04 + 0.12) / 2)
    assert c["median"] == pytest.approx(0.08)
    assert c["ci"] is None
    assert "n too small" in pub.report("smartdoc_qa")


def test_stdout_names_each_table_and_its_reference(pub, capsys):
    fill_smartdoc(pub)
    fill_rdd(pub)
    run(pub)
    out = capsys.readouterr().out
    assert "smartdoc_qa" in out and "human transcription" in out
    assert "rdd" in out and "pseudo ground truth" in out


# --- errors name the culprit and write nothing ---

def test_missing_transcription_is_named(pub, capsys):
    fill_smartdoc(pub)
    pub.write()
    (pub.root / "smartdoc_qa" / "transcriptions" / "s2.txt").unlink()
    assert main(["public", "--root", str(pub.root), "--out", str(pub.out), "--ocr-texts", str(pub.ocr_texts)]) == 1
    assert "s2.txt" in capsys.readouterr().out
    assert not list(pub.out.glob("public_*"))


def test_rdd_scene_without_a_clean_image_is_named(pub, capsys):
    pub.add_rdd("r1_shadow.jpg", "r1", "shadow", REF)
    assert main(pub.argv()) == 1
    out = capsys.readouterr().out
    assert "r1" in out and "clean" in out


def test_rdd_unknown_condition_is_named(pub, capsys):
    fill_rdd(pub)
    pub.add_rdd("r1_dark.jpg", "r1", "dark", REF)
    assert main(pub.argv()) == 1
    assert "dark" in capsys.readouterr().out


def test_empty_pseudo_ground_truth_is_refused(pub, capsys):
    pub.add_rdd("r1_clean.jpg", "r1", "clean", "  \n ")
    pub.add_rdd("r1_shadow.jpg", "r1", "shadow", REF)
    assert main(pub.argv()) == 1
    assert "r1" in capsys.readouterr().out


def test_root_without_datasets_is_an_error(pub, capsys):
    pub.root.mkdir()
    assert main(["public", "--root", str(pub.root), "--out", str(pub.out)]) == 1
    assert "smartdoc_qa" in capsys.readouterr().out


def test_missing_image_is_named(pub, capsys):
    fill_rdd(pub)
    pub.write()
    (pub.root / "rdd" / "images" / "r1_shadow.jpg").unlink()
    assert main(["public", "--root", str(pub.root), "--out", str(pub.out), "--ocr-texts", str(pub.ocr_texts)]) == 1
    assert "r1_shadow.jpg" in capsys.readouterr().out


def test_precomputed_text_missing_for_an_image_is_named(pub, capsys):
    fill_rdd(pub)
    pub.write()
    texts = json.loads(pub.ocr_texts.read_text(encoding="utf-8"))
    del texts["rdd/r1_shadow.jpg"]
    pub.ocr_texts.write_text(json.dumps(texts), encoding="utf-8")
    assert main(["public", "--root", str(pub.root), "--out", str(pub.out), "--ocr-texts", str(pub.ocr_texts)]) == 1
    assert "rdd/r1_shadow.jpg" in capsys.readouterr().out


# --- real OCR path: a fake `tesseract` on PATH counts calls ---

@pytest.fixture
def fake_tesseract(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "ocr_calls.log"
    script = bindir / "tesseract"
    script.write_text(
        '#!/bin/sh\n'
        'if [ "$1" = "--version" ]; then echo "tesseract 9.9.9-fake"; exit 0; fi\n'
        'echo "$1" >> "$FAKE_TESSERACT_LOG"\n'
        'echo "alpha bravo charlie delta"\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_TESSERACT_LOG", str(log))
    return lambda: len(log.read_text().split()) if log.exists() else 0


def test_rerun_does_not_repeat_ocr_for_unchanged_images(pub, fake_tesseract):
    fill_smartdoc(pub)
    fill_rdd(pub)
    assert main(pub.argv(precomputed=False)) == 0
    first = fake_tesseract()
    assert first == 8
    assert main(pub.argv(precomputed=False)) == 0
    assert fake_tesseract() == first
    assert pub.summary("smartdoc_qa")["header"]["tesseract"] == "tesseract 9.9.9-fake"


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_smoke_transcription_with_real_tesseract(pub):
    pub.add_smartdoc("s1_blur_1.jpg", "s1", SD_CLASSES[0], "blur", "x", "x")
    pub.write()
    d = pub.root / "smartdoc_qa"
    Image.open("data/raw/smoke_render.png").convert("RGB").save(d / "images" / "s1_blur_1.jpg", quality=95)
    shutil.copy("data/pdf/smoke.txt", d / "transcriptions" / "s1.txt")
    assert main(["public", "--root", str(pub.root), "--out", str(pub.out)]) == 0
    c = cell(pub.summary("smartdoc_qa"), "blur", SD_CLASSES[0])
    assert c["n"] == 1 and c["mean"] < 0.1
    assert pub.summary("smartdoc_qa")["header"]["tesseract"].startswith("tesseract 5")
