# Stage 1 Decisions (grill results)

## Page selection
- 36 pages in total, all English, mostly plain text, no formulas or large figures. Paper 12 (single-column 6 / two-column 6), book page 10, table 8, receipt 6.
- Receipts and tables are typeset by ourselves in LaTeX/HTML and exported, which guarantees a text layer; for table pages check the pdftotext reading order and swap the page if it is scrambled.
- Font sizes spread out: paper 9–10pt, book page 11–12pt, receipt 8–9pt monospace, table 8–10pt.

## Capture protocol
- Phone A shoots odd pages, B shoots even pages; each document type is split half and half between the two phones.
- Clean baseline: phone on a stand shooting straight down; ceiling light of the same room; dark tablecloth.
- Blur, 3 shots: one each of horizontal translation / vertical hand shake / diagonal shooting while walking; record the direction class.
- Perspective: protractor template taped to the desk, 15°/30°/45°, tolerance ±5°.
- Combo, 2 shots: one with a hard shadow, one with a soft shadow.
- Raw images keep their pixels: no scaling or cropping; rotate upright by EXIF when reading.

## Naming and metadata
- File name `p07_blur_2.jpg`; condition codes clean / blur / shadow / persp / combo; the sequence number starts at 1 within each condition of each page.
- CSV fields: filename, page_id, doc_type, condition, seq, phone_model, light, angle_deg, blur_dir, shadow_type, split, captured_at, resolution, pilot, notes. split is written by the script.

## Split
- 12 tuning / 24 test, stratified by type (paper 4/8, book 3/7, table 3/5, receipt 2/4), seed 253.
- Phones roughly balanced on both sides, with at most one redraw before shooting; once the split file is generated it is committed and not changed again. Pilot pages are taken from the tuning set.

## Pilot
- 4 pages (1 per type) × 3 shots each of clean/blur/shadow/perspective, about 40 images.
- Pass: the condition's mean CER is ≥5 percentage points above the clean baseline, and ≥2/3 of the images are above the page's baseline; for pages whose baseline is already poor, look at ≥1.5× instead.
- If it fails, reshoot only that condition with heavier defects. Pilot images are kept, with pilot=true.

## Public datasets
- SmartDoc-QA is the main one (Zenodo, CC BY 4.0, about 13.7 GB, take only a portion each of blur/lighting/perspective), keeping its three document classes.
- SmartDoc Ch.1 sample (21 MB) is used only for the corner success rate.
- Shadow uses RDD (Google Drive, license not stated); DocUNet and Hradiš are not done for now.
- There is no suitable public set of real blurred documents: use self-collected + synthetic blur instead.
- Each of the three reference-text sources gets its own table (see ADR-0002); RDD uses only pseudo ground truth and is interpreted only as relative improvement.
- To-do before downloading: notify icdar.smartdoc@gmail.com of the use (the authors' request); re-check licenses against the original pages.

## Baseline convention
- The baseline (P0) runs on all 36 pages; the preprocessing evaluation reports only the test set.
- Main table: condition × document type; within a cell, first average within the same page and condition, then average over pages; show n and the median; no interval for n<5, otherwise a by-page bootstrap 95% interval.
- If the receipt clean-baseline CER is >20%, keep it but discuss it separately and do not fold it into the overall average.

## Completion criteria
About 360 images + metadata CSV; the baseline CER of the blur/shadow/perspective conditions is clearly above the clean baseline, otherwise reshoot.
