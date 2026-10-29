Status: ready-for-agent

# Stage 1: Data Collection and Baseline — Data Toolchain Spec

## Problem Statement

I want to study why phone-photographed documents hurt OCR. Stage 1 collects about 360 self-collected images (36 pages × 12 shots per page) and produces the baseline CER/WER without any preprocessing (P0). Right now there is only a single-image evaluation script: there is no way to check whether the captured data follows the protocol, no reproducible by-page tuning/test split, no baseline report aggregated by "condition × document type", and no way to judge objectively whether a defect is "clearly above the clean baseline" and therefore whether to reshoot.

## Solution

Provide a command-line entry point that takes the metadata CSV, the image directory and the PDF directory and does three things: validate that the data follows the capture protocol; make a stratified by-page split with a fixed seed and write it back to the CSV; run the P0 OCR evaluation on all images and output a "condition × document type" baseline report, together with the pass/fail verdict for the pilot batch. The evaluation convention follows ADR-0001, and the CER of public datasets goes in separate tables per ADR-0002.

## User Stories

1. As a researcher, I want the metadata CSV validated against the capture protocol, so that I catch naming or labeling mistakes before spending time on OCR.
2. As a researcher, I want filenames checked against `p<page>_<condition>_<seq>.jpg` and against the CSV rows, so that no image is orphaned or missing a row.
3. As a researcher, I want condition codes restricted to clean / blur / shadow / persp / combo, so that typos don't create phantom conditions.
4. As a researcher, I want each page's counts checked (1 clean, 3 blur, 3 shadow, 3 persp, 2 combo), so that I know which shots are missing.
5. As a researcher, I want each page's PDF source and page number linked in the data, so that ground truth can be extracted automatically.
6. As a researcher, I want ground truth extracted via pdftotext with the shared normalization, so that all CER/WER values are comparable.
7. As a researcher, I want a warning when a page's extracted text is empty or suspiciously short, so that I replace pages without a usable text layer.
8. As a researcher, I want a warning for table pages whose reading order looks scrambled, so that I can replace them.
9. As a researcher, I want pages split into tuning/test sets with a fixed seed (253), so that the split is reproducible.
10. As a researcher, I want the split stratified by document type (paper 4/8, book 3/7, table 3/5, receipt 2/4), so that every type appears on both sides.
11. As a researcher, I want the split to report the phone balance on each side, so that I can redraw once before shooting if it is lopsided.
12. As a researcher, I want the split written back to the CSV and refused to be overwritten once committed, so that tuning never leaks into testing.
13. As a researcher, I want all images of one page guaranteed on the same side, so that no page straddles the split.
14. As a researcher, I want pilot images flagged in the CSV and kept in the data, so that they count if the protocol matched.
15. As a researcher, I want pilot pages drawn from the tuning set, so that pilot shooting cannot contaminate the test set.
16. As a researcher, I want P0 OCR run on every image with the fixed Tesseract settings, so that baselines are measured consistently.
17. As a researcher, I want the tesseract version, PSM/OEM, and normalization version recorded in every result file, so that runs are auditable.
18. As a researcher, I want per-image CER/WER kept as the raw data, so that every aggregate can be recomputed.
19. As a researcher, I want per-image results to be cached, so that re-running the report does not redo OCR on unchanged images.
20. As a researcher, I want a condition × document-type table, so that I can see where each defect hurts which kind of page.
21. As a researcher, I want each cell computed as page-level means (average the images of a page+condition first, then pages), so that blur's three shots do not outweigh other conditions.
22. As a researcher, I want each cell to show n and the median, so that thin cells are visible.
23. As a researcher, I want a bootstrap-by-page 95% interval for cells with n ≥ 5, and "n too small" otherwise, so that I do not over-read small samples.
24. As a researcher, I want micro-averages in an appendix table, so that I can cross-check the macro numbers.
25. As a researcher, I want a per-page CER distribution plot, so that outlier pages are visible.
26. As a researcher, I want the receipt type flagged when its clean-baseline CER exceeds 20%, so that I discuss it separately instead of folding it into totals.
27. As a researcher, I want a pilot verdict per condition (mean CER ≥ 5 points above the clean baseline and ≥ 2/3 of images above their page's clean CER; ≥ 1.5× for pages whose baseline is already poor), so that I know objectively which conditions to reshoot.
28. As a researcher, I want the verdict to say which condition failed and by how much, so that I know how much heavier to make the defect.
29. As a researcher, I want baseline stage-exit status (blur, shadow, persp each clearly above clean), so that I can tell whether stage 1 is complete.
30. As a researcher, I want the baseline run on all 36 pages while later evaluation reports only the test set, so that the baseline serves as evidence of harm without touching tuning.
31. As a researcher, I want public-dataset results written to separate tables by reference source (pdftotext, human transcription, pseudo ground truth), so that differing reference quality is never averaged together.
32. As a researcher, I want pseudo-ground-truth tables labeled as relative-improvement only, so that they are not misread as true accuracy.
33. As a researcher, I want SmartDoc-QA results grouped by its own three document types, so that they stay comparable to its published structure.
34. As a researcher, I want a checklist for each public dataset (URL, download method, size, license, citation, ground-truth availability, used-for), so that licensing is checked before use.
35. As a researcher, I want the SmartDoc authors' request to be told of the usage recorded in the checklist, so that I comply with it.
36. As a researcher, I want raw images never modified (only EXIF orientation applied when reading), so that effective DPI is unchanged for OCR.
37. As a researcher, I want clear error messages that name the offending file or row, so that I can fix problems quickly.

## Implementation Decisions

- One high-level entry point (CLI) takes the metadata CSV, the image directory, and the PDF directory, and has modes for validate, split, and baseline-report. Lower-level pieces (normalization, scoring, OCR wrapper, PDF ground truth) already exist and are reused unchanged.
- Page is the unit of the data. File names are `p<page>_<condition>_<seq>.jpg`; condition codes are clean, blur, shadow, persp, combo; seq starts at 1 within each page+condition.
- CSV fields: filename, page_id, doc_type, condition, seq, phone_model, light, angle_deg, blur_dir, shadow_type, split, captured_at, resolution, pilot, notes. The split field is written by the tool, never by hand.
- The CSV also needs a link from page to its source PDF and PDF page, so ground truth can be derived.
- Corpus: 36 English pages with a text layer; paper 12 (6 single-column, 6 two-column), book 10, table 8, receipt 6.
- Split: 12 tuning / 24 test, stratified by document type, seed 253, phones roughly balanced on both sides; at most one redraw before shooting; once written, the split file is committed and never regenerated. Pilot pages are chosen from the tuning set.
- Capture protocol: phone A takes odd pages and phone B even pages, balanced within each document type; clean baseline from a fixed mount; blur 3 shots (horizontal, vertical, diagonal); perspective at 15/30/45° (±5°); combo 2 shots (one hard shadow, one soft shadow). Raw images keep native pixels.
- Aggregation: per-image CER/WER is the raw data; cells are page-level means (images within page+condition first); report n and median; bootstrap-by-page 95% CI when n ≥ 5; micro-average in an appendix; per-page distribution plotted.
- Pilot verdict rule as in user story 27. Failing conditions are reshot alone with heavier defects; pilot images are retained with pilot=true.
- Public data: SmartDoc-QA is the main public set (subset of blur/light/perspective); SmartDoc Ch.1 sample only for corner-detection success; RDD for shadow using pseudo ground truth; DocUNet and Hradiš not used for now. Result tables are separated per ADR-0002.
- Result files record the tesseract version, PSM/OEM, and normalization version in their header (ADR-0001).

## Testing Decisions

- A good test exercises only external behavior: given a small fake dataset (a few synthetic images, a tiny text-layer PDF, a hand-written CSV), assert on the tool's outputs — validation messages, written split, report tables, pilot verdicts — never on internals.
- The single seam is the CLI-level entry point above. No new lower seams are introduced; the existing unit tests for normalization and scoring remain where they are.
- Cases to cover: valid dataset passes; misnamed file, missing row, wrong per-page counts, unknown condition each produce a message naming the culprit; split is stratified, reproducible with the seed, keeps pages whole, refuses to overwrite; report cells use page-level means, show n/median, drop intervals when n < 5; pilot verdict passes and fails on crafted CERs; receipt flag at the 20% threshold.
- The OCR call may be replaced with precomputed per-image results in tests so they run without Tesseract; one smoke test uses real Tesseract on the existing smoke PDF.
- Prior art: the existing unit tests for normalization/scoring and the ground-truth test, which already use small in-repo fixtures.

## Out of Scope

- Any preprocessing method (Wiener, background division, homography) — stages 2+.
- The P0–P6 order experiments, synthetic data generation, PSNR/SSIM.
- PaddleOCR or any AI reference model.
- Downloading or processing DocUNet or Hradiš data; the Kligler data.
- Physically photographing the pages and printing the PDFs (human work).

## Further Notes

- Sources of truth: `docs/stage1-decisions.md`, ADR-0001, ADR-0002, and `CONTEXT.md` terms (Page, Clean baseline, Combo set, Pilot batch, Pseudo ground truth, Human transcription).
- Receipt pages may have a low clean-baseline CER ceiling; discuss separately rather than dropping.
- Before using public datasets: notify the SmartDoc authors of usage and re-verify licenses on the original pages.
- Stage-1 exit: about 360 images plus CSV, with blur, shadow, and perspective baselines clearly above the clean baseline; otherwise reshoot.
