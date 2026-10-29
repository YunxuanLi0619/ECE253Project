# 03: P0 baseline scoring, report and pilot verdict

**What to build:** The command-line entry point runs the P0 evaluation on all images with the fixed Tesseract configuration (ADR-0001), saves each image's CER/WER as raw data, and records the tesseract version, PSM/OEM and normalization version in the result file header; unchanged images do not rerun OCR. It then outputs the baseline report from these: a "condition × document type" table whose cells first average within the same page and condition and then over pages, showing n and the median, giving a by-page bootstrap 95% interval only for n ≥ 5 and otherwise writing "n too small"; micro-averages in an appendix table; a per-page CER distribution plot; types whose clean-baseline CER exceeds 20% (such as receipts) get a flag. It also gives the pilot verdict: a condition passes if its mean CER is ≥ 5 percentage points above the clean baseline and ≥ 2/3 of its images are above the page's baseline (for pages whose baseline is already poor, look at ≥ 1.5× instead), pointing out which condition failed and by how much; and it reports whether blur, shadow and perspective are all clearly above the clean baseline (the stage exit status).

**Blocked by:** 01

**Status:** ready-for-agent

- [x] The result file header contains the tesseract version, PSM/OEM and normalization version
- [x] A rerun calls OCR only for new or changed images
- [x] Cell values are computed as page-level means and show n and the median; no interval for n < 5
- [x] The micro-average appendix table and the per-page distribution plot are generated
- [x] Types with clean-baseline CER > 20% are flagged
- [x] The pilot verdict gives pass and fail on crafted CERs and explains the failing condition and the gap
- [x] Tests go through the command-line entry point, with OCR results replaceable by precomputed numbers; plus one smoke test with real Tesseract on the existing smoke PDF

## Comments

Implementation done (`python -m eval.cli report --csv … --images … --pdfs … --out …`, code in `src/eval/{baseline,report,plot,cli}.py`, tests in `tests/test_report.py`). Trade-offs in the verdict details:
- "Baseline already poor" = the page's clean CER > 20% (the same threshold as the receipt flag); this changes only the per-image criterion (≥ 1.5×), the mean gap is still ≥ 5 percentage points.
- The stage exit status uses the same verdict rule, computed over all pages.
- `--precomputed FILE` (filename → {cer, wer}) can replace OCR; this mode does not write `p0_results.json`.
- Tesseract does not read the EXIF orientation, so images carrying an orientation tag are rotated upright before OCR (a temporary copy; the original is untouched).
