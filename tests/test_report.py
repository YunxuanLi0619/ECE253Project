"""Baseline report through the CLI entry point; OCR numbers are precomputed so no Tesseract is needed."""
import json
import os
import shutil
from pathlib import Path

import pytest
from PIL import Image

from eval import NORMALIZE_VERSION
from eval.cli import main
from fakedata import Capture


@pytest.fixture
def cap(tmp_path):
    return Capture(tmp_path)


def run(cap, *extra) -> dict:
    assert main(cap.argv(*extra)) == 0
    return cap.summary()


def cell(summary, cond, doc_type, metric="cer"):
    return summary["cells"][metric][cond][doc_type]


def test_cell_is_page_level_mean_with_n_and_median(cap):
    # page means 0.2, 0.6, 0.1: macro 0.3 (an image-level mean would be 0.26), median 0.2
    cap.add_page(1, "paper", {"clean": [0.0], "blur": [0.1, 0.1, 0.4]})
    cap.add_page(2, "paper", {"clean": [0.0], "blur": [0.6]})
    cap.add_page(3, "paper", {"clean": [0.0], "blur": [0.1]})
    c = cell(run(cap), "blur", "paper")
    assert c["n"] == 3
    assert c["mean"] == pytest.approx(0.3)
    assert c["median"] == pytest.approx(0.2)


def test_no_interval_below_five_pages(cap, capsys):
    for p in range(1, 5):
        cap.add_page(p, "paper", {"clean": [0.0], "blur": [0.1 * p]})
    s = run(cap)
    assert cell(s, "blur", "paper")["n"] == 4
    assert cell(s, "blur", "paper")["ci"] is None
    assert "n too small" in (cap.out / "baseline_report.md").read_text(encoding="utf-8")


def test_interval_from_five_pages_is_reproducible(cap):
    values = [0.1, 0.2, 0.3, 0.5, 0.9]
    for p, v in enumerate(values, start=1):
        cap.add_page(p, "paper", {"clean": [0.0], "blur": [v]})
    first = cell(run(cap), "blur", "paper")
    lo, hi = first["ci"]
    assert first["n"] == 5
    assert min(values) <= lo <= first["mean"] <= hi <= max(values)
    assert cell(run(cap), "blur", "paper")["ci"] == [lo, hi]


def test_micro_average_and_plot_are_produced(cap):
    cap.add_page(1, "paper", {"clean": [0.0], "blur": [0.1, 0.3]})
    s = run(cap)
    assert s["micro"]["cer"]["blur"]["paper"]["value"] == pytest.approx(0.2)
    assert s["micro"]["cer"]["blur"]["paper"]["n_images"] == 2
    assert (cap.out / "cer_by_page.png").read_bytes().startswith(b"\x89PNG")
    md = (cap.out / "baseline_report.md").read_text(encoding="utf-8")
    assert "Micro-Average" in md and "cer_by_page.png" in md


def test_receipt_flagged_when_clean_cer_over_20_percent(cap, capsys):
    cap.add_page(1, "paper", {"clean": [0.05], "blur": [0.3]})
    cap.add_page(2, "receipt", {"clean": [0.25], "blur": [0.6]})
    s = run(cap)
    assert s["flagged_types"] == ["receipt"]
    assert "receipt" in capsys.readouterr().out
    # the flagged type stays in its own column but is left out of the pooled column
    assert cell(s, "blur", "receipt")["mean"] == pytest.approx(0.6)
    assert cell(s, "blur", "overall")["mean"] == pytest.approx(0.3)
    assert "receipt ⚠" in (cap.out / "baseline_report.md").read_text(encoding="utf-8")


def test_receipt_at_exactly_20_percent_is_not_flagged(cap):
    cap.add_page(1, "receipt", {"clean": [0.20], "blur": [0.6]})
    assert run(cap)["flagged_types"] == []


def pilot_page(cap, page, doc_type, clean, **shots):
    cap.add_page(page, doc_type, {"clean": [clean], **shots}, pilot=True)


def test_pilot_passes_when_all_conditions_clearly_worse(cap, capsys):
    pilot_page(cap, 1, "paper", 0.02, blur=[0.30, 0.20, 0.25], shadow=[0.2, 0.2, 0.2], persp=[0.4, 0.4, 0.4])
    pilot_page(cap, 2, "book", 0.04, blur=[0.30, 0.25, 0.28], shadow=[0.2, 0.2, 0.2], persp=[0.4, 0.4, 0.4])
    s = run(cap)
    assert all(v["passed"] for v in s["pilot"].values())
    assert "Pilot verdict: PASS" in capsys.readouterr().out


def test_pilot_failure_names_condition_and_shortfall(cap, capsys):
    # shadow only +2 points over clean on average: fails the 5-point rule by 3 points
    pilot_page(cap, 1, "paper", 0.02, blur=[0.3] * 3, shadow=[0.04, 0.04, 0.04], persp=[0.4] * 3)
    pilot_page(cap, 2, "book", 0.02, blur=[0.3] * 3, shadow=[0.04, 0.04, 0.04], persp=[0.4] * 3)
    s = run(cap)
    assert s["pilot"]["blur"]["passed"] and s["pilot"]["persp"]["passed"]
    shadow = s["pilot"]["shadow"]
    assert not shadow["passed"]
    assert shadow["gap"] == pytest.approx(0.02)
    assert shadow["gap_shortfall"] == pytest.approx(0.03)
    out = capsys.readouterr().out
    assert "Pilot verdict: FAIL" in out
    assert "shadow: FAIL" in out and "3.0" in out
    assert "blur: pass" in out


def test_pilot_needs_two_thirds_of_images_above_their_page_baseline(cap):
    # mean gap is large (one huge outlier) but only 1 of 3 images is above its clean baseline
    pilot_page(cap, 1, "paper", 0.10, blur=[0.05, 0.05, 0.90], shadow=[0.3] * 3, persp=[0.3] * 3)
    s = run(cap)
    blur = s["pilot"]["blur"]
    assert blur["gap"] > 0.05 and not blur["passed"]
    assert blur["n_above"] == 1 and blur["n_images"] == 3


def test_pilot_boundaries_are_inclusive(cap):
    # exactly +5 points; exactly 2 of 3 images above the baseline
    pilot_page(cap, 1, "paper", 0.10, blur=[0.05, 0.20, 0.20], shadow=[0.3] * 3, persp=[0.3] * 3)
    blur = run(cap)["pilot"]["blur"]
    assert blur["gap"] == pytest.approx(0.05)
    assert blur["n_above"] == 2 and blur["n_images"] == 3 and blur["passed"]


def test_poor_baseline_page_needs_one_and_a_half_times(cap):
    # clean CER 0.40 is poor: 0.50 is above the baseline but under 1.5x (0.60)
    pilot_page(cap, 1, "receipt", 0.40, blur=[0.50, 0.50, 0.50], shadow=[0.7] * 3, persp=[0.7] * 3)
    s = run(cap)
    assert s["pilot"]["blur"]["n_above"] == 0 and not s["pilot"]["blur"]["passed"]
    assert s["pilot"]["shadow"]["passed"]


def test_pilot_judges_only_pilot_images_and_stage_exit_judges_all(cap):
    pilot_page(cap, 1, "paper", 0.02, blur=[0.3] * 3, shadow=[0.3] * 3, persp=[0.3] * 3)
    cap.add_page(2, "book", {"clean": [0.02], "blur": [0.02] * 3, "shadow": [0.3] * 3, "persp": [0.3] * 3})
    s = run(cap)
    assert s["pilot"]["blur"]["n_images"] == 3  # page 2 is not pilot
    assert s["stage_exit"]["blur"]["n_images"] == 6
    assert s["stage_exit"]["blur"]["gap"] == pytest.approx(0.14)
    assert not s["stage_exit"]["blur"]["passed"]  # page 2's blur shots equal its clean CER
    assert s["stage_exit"]["shadow"]["passed"]


def test_no_pilot_images_means_no_pilot_verdict(cap, capsys):
    cap.add_page(1, "paper", {"clean": [0.02], "blur": [0.3]})
    assert run(cap)["pilot"] is None


def test_stage_exit_says_which_defect_is_not_clearly_above_clean(cap, capsys):
    cap.add_page(1, "paper", {"clean": [0.02], "blur": [0.3], "shadow": [0.03], "persp": [0.3]})
    s = run(cap)
    assert not s["stage_exit"]["shadow"]["passed"] and s["stage_exit"]["blur"]["passed"]
    assert "Stage exit" in capsys.readouterr().out


def test_missing_precomputed_number_names_the_image(cap, capsys):
    cap.add_page(1, "paper", {"clean": [0.02]})
    argv = cap.argv()
    cap.precomputed.write_text("{}", encoding="utf-8")
    assert main(argv) == 1
    assert "p01_clean_1.jpg" in capsys.readouterr().out


# --- real OCR path: a fake `tesseract` on PATH counts calls; one smoke test uses the real binary ---

@pytest.fixture
def fake_tesseract(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "ocr_calls.log"
    script = bindir / "tesseract"
    script.write_text(
        '#!/bin/sh\n'
        'if [ "$1" = "--version" ]; then echo "tesseract $FAKE_TESSERACT_VERSION"; exit 0; fi\n'
        'echo "$1" >> "$FAKE_TESSERACT_LOG"\n'
        'echo "Motion blur, shadows and perspective"\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_TESSERACT_LOG", str(log))
    monkeypatch.setenv("FAKE_TESSERACT_VERSION", "9.9.9-fake")

    class Fake:
        def calls(self) -> list[str]:
            return [Path(p).name for p in log.read_text().split()] if log.exists() else []

    return Fake()


def test_results_file_header_records_tool_and_protocol(cap, fake_tesseract):
    cap.add_page(1, "paper", {"clean": [0.0]})
    assert main(cap.argv(precomputed=False)) == 0
    stored = json.loads((cap.out / "p0_results.json").read_text(encoding="utf-8"))
    assert stored["header"]["tesseract"] == "tesseract 9.9.9-fake"
    assert stored["header"]["ocr_config"] == {"psm": 3, "oem": 1, "lang": "eng"}
    assert stored["header"]["normalize_version"] == NORMALIZE_VERSION
    assert 0 < stored["images"]["p01_clean_1.jpg"]["cer"] < 1  # raw per-image data kept
    md = (cap.out / "baseline_report.md").read_text(encoding="utf-8")
    assert "9.9.9-fake" in md and "psm" in md


def test_rerun_ocrs_only_new_or_changed_images(cap, fake_tesseract, capsys):
    cap.add_page(1, "paper", {"clean": [0.0], "blur": [0.0, 0.0]})
    assert main(cap.argv(precomputed=False)) == 0
    assert sorted(fake_tesseract.calls()) == ["p01_blur_1.jpg", "p01_blur_2.jpg", "p01_clean_1.jpg"]

    assert main(cap.argv(precomputed=False)) == 0
    assert len(fake_tesseract.calls()) == 3  # nothing re-run
    assert "OCR run on 0 image(s), 3 reused" in capsys.readouterr().out

    cap.add_page(2, "book", {"clean": [0.0]})
    Image.new("RGB", (8, 8), "black").save(cap.images / "p01_blur_2.jpg")  # retaken photo
    assert main(cap.argv(precomputed=False)) == 0
    assert sorted(fake_tesseract.calls()[3:]) == ["p01_blur_2.jpg", "p02_clean_1.jpg"]


def test_changed_tesseract_version_invalidates_stored_results(cap, fake_tesseract, monkeypatch):
    cap.add_page(1, "paper", {"clean": [0.0]})
    assert main(cap.argv(precomputed=False)) == 0
    monkeypatch.setenv("FAKE_TESSERACT_VERSION", "9.9.10-fake")
    assert main(cap.argv(precomputed=False)) == 0
    assert len(fake_tesseract.calls()) == 2


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_smoke_pdf_with_real_tesseract(cap):
    shutil.copy("data/pdf/smoke.pdf", cap.pdfs / "smoke.pdf")
    cap.add_page(1, "paper", {"clean": [0.0]})
    Image.open("data/raw/smoke_render.png").convert("RGB").save(cap.images / "p01_clean_1.jpg", quality=95)
    cap.rows[0]["pdf_file"] = "smoke.pdf"
    assert main(cap.argv(precomputed=False)) == 0
    stored = json.loads((cap.out / "p0_results.json").read_text(encoding="utf-8"))
    assert stored["header"]["tesseract"].startswith("tesseract 5")
    assert stored["images"]["p01_clean_1.jpg"]["cer"] < 0.1
    assert cap.summary()["cells"]["cer"]["clean"]["paper"]["n"] == 1


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_exif_rotated_photo_is_read_upright(cap):
    shutil.copy("data/pdf/smoke.pdf", cap.pdfs / "smoke.pdf")
    cap.add_page(1, "paper", {"clean": [0.0]})
    cap.rows[0]["pdf_file"] = "smoke.pdf"
    page = Image.open("data/raw/smoke_render.png").convert("RGB").resize((1275, 1650))
    exif = Image.Exif()
    exif[0x0112] = 6  # pixels are stored turned 90 degrees CCW; the tag says to turn them back
    page.rotate(90, expand=True).save(cap.images / "p01_clean_1.jpg", quality=90, exif=exif)
    assert main(cap.argv(precomputed=False)) == 0
    stored = json.loads((cap.out / "p0_results.json").read_text(encoding="utf-8"))
    assert stored["images"]["p01_clean_1.jpg"]["cer"] < 0.1


# --- ticket 05: a poor-baseline (flagged) type is left out of the verdicts and reported on its own ---

def flagged_capture(cap):
    """2 paper pages with a clear defect effect; 3 receipt pages whose clean CER (0.9) is above everything."""
    for p in (1, 2):
        cap.add_page(p, "paper", {"clean": [0.02], "blur": [0.3] * 3, "shadow": [0.3] * 3, "persp": [0.3] * 3})
    for p in (3, 4, 5):
        cap.add_page(p, "receipt", {"clean": [0.9], "blur": [0.95] * 3, "shadow": [0.5] * 3, "persp": [0.95] * 3})


def test_flagged_type_does_not_fail_the_stage_exit(cap, capsys):
    flagged_capture(cap)
    s = run(cap)
    assert s["flagged_types"] == ["receipt"]
    assert all(v["passed"] for v in s["stage_exit"].values())
    assert s["stage_exit"]["shadow"]["n_pages"] == 2  # only the paper pages were judged
    stage_line = next(l for l in capsys.readouterr().out.splitlines() if l.startswith("Stage exit"))
    assert stage_line.endswith(": PASS")


def test_report_names_excluded_types_and_lists_their_gaps_separately(cap, capsys):
    flagged_capture(cap)
    s = run(cap)
    out = capsys.readouterr().out
    assert "excluded" in out and "receipt" in out
    gaps = s["flagged_verdicts"]["receipt"]
    assert gaps["shadow"]["gap"] == pytest.approx(-0.4)
    assert gaps["blur"]["gap"] == pytest.approx(0.05)
    md = (cap.out / "baseline_report.md").read_text(encoding="utf-8")
    assert "Excluded" in md and "receipt" in md and "not counted" in md


def test_stage_exit_is_unchanged_when_no_type_is_flagged(cap, capsys):
    cap.add_page(1, "paper", {"clean": [0.02], "blur": [0.3] * 3, "shadow": [0.3] * 3, "persp": [0.3] * 3})
    cap.add_page(2, "book", {"clean": [0.04], "blur": [0.3] * 3, "shadow": [0.3] * 3, "persp": [0.3] * 3})
    s = run(cap)
    assert s["flagged_types"] == [] and s["flagged_verdicts"] == {}
    assert s["stage_exit"]["blur"]["n_pages"] == 2
    assert s["stage_exit"]["blur"]["gap"] == pytest.approx(0.27)
    assert "excluded" not in capsys.readouterr().out
    assert "Excluded" not in (cap.out / "baseline_report.md").read_text(encoding="utf-8")


def test_pilot_verdict_keeps_flagged_types_under_the_poor_baseline_rule(cap):
    pilot_page(cap, 1, "paper", 0.02, blur=[0.3] * 3, shadow=[0.3] * 3, persp=[0.3] * 3)
    pilot_page(cap, 2, "receipt", 0.9, blur=[0.95] * 3, shadow=[0.5] * 3, persp=[0.95] * 3)
    s = run(cap)
    assert s["pilot"]["shadow"]["n_pages"] == 2 and not s["pilot"]["shadow"]["passed"]


def test_few_judged_pages_get_a_sample_size_hint(cap, capsys):
    for p in (1, 2):
        cap.add_page(p, "paper", {"clean": [0.02], "blur": [0.3] * 3, "shadow": [0.3] * 3, "persp": [0.3] * 3})
    run(cap)
    assert "Too few pages" in (cap.out / "baseline_report.md").read_text(encoding="utf-8")
    assert "few pages" in capsys.readouterr().out

    cap.add_page(3, "paper", {"clean": [0.02], "blur": [0.3] * 3, "shadow": [0.3] * 3, "persp": [0.3] * 3})
    run(cap)
    assert "Too few pages" not in (cap.out / "baseline_report.md").read_text(encoding="utf-8")
