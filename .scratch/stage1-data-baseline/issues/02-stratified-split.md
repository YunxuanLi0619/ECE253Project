# 02: Stratified by-page split

**What to build:** The command-line entry point can split the pages into a tuning set and a test set stratified by document type (12/24 for 36 pages: paper 4/8, book 3/7, table 3/5, receipt 2/4), with the seed fixed at 253, all images of one page on the same side, and write the result back to the CSV's split field. It outputs the distribution of the two phones on both sides; once the split file is generated, further overwriting is refused. Pilot pages may only come from the tuning set.

**Blocked by:** 01

**Status:** done (pending review)

- [x] The same seed gives the same split on repeated runs
- [x] Every document type has pages on both sides, and images of the same page do not cross sides
- [x] The share of the two phones on both sides is output
- [x] Running again when a split exists is refused with an explanation, without overwriting
- [x] Pilot pages (pilot) can only land in the tuning set
- [x] Tests go only through the command-line entry point, using a small fake dataset

## Comments

- Implementation: `python -m eval.cli split --csv meta.csv` (`src/eval/cli.py`, `split_dataset` in `src/eval/dataset.py`), tests in `tests/test_split.py` (11 cases, CLI only), fake CSV built in `tests/fakedata.py::write_page_csv`.
- Decisions: split needs only the CSV, not the image/PDF directories. Tuning pages per type = round(pages of that type / 3) (exactly 4/3/3/2 for 36 pages); a type with fewer than 2 pages, an unknown doc_type, or a type with more pilot pages than tuning slots all raise an error and leave the file unchanged. Any existing non-empty split is refused (exit code 1). The seed is fixed at 253 (`SPLIT_SEED`) and the draw is made after sorting by page id, independent of CSV row order. The phone share uses the first non-empty `phone_model` within the page, and unknown if empty.
- Not done: "at most one redraw before shooting" has no command-line support for now (it conflicts with "refuse to overwrite once generated"); to redraw, manually clear the split column and run again.
- The current directory is not a git repository, so nothing was committed.
