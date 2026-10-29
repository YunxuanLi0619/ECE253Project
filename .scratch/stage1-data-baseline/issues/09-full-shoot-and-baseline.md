# 09: Finish shooting 360 images and produce the formal baseline

**What to build:** Manual work plus one run. After the pilot passes, shoot all remaining pages (36 pages, 432 images in total, including the retained pilot images), complete the CSV, and put everything in `data/raw/`. Run `validate` until 0 errors; run `report` on all 36 pages and write the output to `results/stage1-baseline/`. Check that the CER of all three defects is clearly above the clean baseline (the exit status passes after the 05 fix); for conditions with only a small difference, reshoot only that condition. After saving the report, treat `p0_results.json` as read-only raw data and no longer edit the numbers by hand.

**Blocked by:** 05, 08

**Status:** ready-for-human

- [ ] All 36 pages shot, 12 images per page, with names corresponding one-to-one with the CSV
- [ ] `validate` has 0 errors; warnings (short text layer, table reading order) are handled one by one
- [ ] `report` output is in `results/stage1-baseline/`: `p0_results.json`, `baseline_report.md`, `baseline_summary.json`, `cer_by_page.png`
- [ ] Stage exit status: blur, shadow and persp all pass; if not, that condition has been reshot and rerun
- [ ] Types with clean-baseline CER > 20% are discussed separately in the report
- [ ] Later evaluations report only the test set (24 pages); this baseline reports all 36 pages

## Comments

- Corresponds to the three deliverables and the completion criteria of stage 1: about 360 self-collected images, the metadata CSV, and the baseline CER for each condition.
- When done, the self-collected part of stage 1 can be declared complete; for the public-dataset part see 10 and 11.
