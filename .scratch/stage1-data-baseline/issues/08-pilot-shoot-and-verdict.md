# 08: Pilot batch shoot and pilot verdict

**What to build:** Manual work. Once the page list is settled, first generate the CSV skeleton with 06 and make the split with 02. Pick 2–3 pages from the tuning set (one each of paper, book page and table is suggested), shoot 12 images per page per the protocol, mark `pilot` as true for these pages in the CSV, and fill in light, captured_at and the other fields. Put the images in `data/raw/`, run `validate` and then `report`, and read the pilot verdict. If a condition fails (mean CER less than 5 percentage points above the clean baseline, or fewer than 2/3 of the images above the page's baseline), reshoot only that condition with heavier defects. Take care not to make the defect so heavy that the text is entirely unrecognizable: a CER close to 100% is equally useless for the later deblurring experiments, and the target range is about 30%–70%.

**Blocked by:** 06, 07

**Status:** ready-for-human

- [ ] 2–3 pilot pages taken from the tuning set, 12 images each, pilot=true in the CSV
- [ ] `validate` passes (0 errors)
- [ ] `report` runs through on the real images, and the OCR time per image is noted
- [ ] Clean-image CER is reasonable (single digits for paper pages); if very high, first check orientation, the text layer and whether the shoot is complete
- [ ] The pilot verdicts of blur, shadow and perspective all "pass", otherwise reshoot per condition and update the CSV
- [ ] Pick 2–3 images, run the `tesseract` command line by hand, and compare with the CER in `p0_results.json`

## Comments

- Quick single-image trial: `python -m eval.run data/raw/xxx.jpg data/pdf/xxx.pdf --page N`.
- Pilot images that pass are kept and count toward the formal data; `split` cannot be overwritten once written, so do `split` once after the page selection is final and before the pilot.
