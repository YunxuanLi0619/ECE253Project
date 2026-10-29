# 01: Metadata validation

**What to build:** Given the metadata CSV, the image directory and the PDF directory, the command-line entry point can tell whether the self-collected data follows the capture protocol, and gives an error message that names the culprit for every problem. What is validated: file names match `p<page>_<condition>_<seq>.jpg` and correspond one-to-one with the CSV rows; condition codes are only clean / blur / shadow / persp / combo; the per-page counts are 1/3/3/3/2; every page can be linked to its source PDF and page number and its ground truth extracted successfully (through the shared normalization); a warning when the text layer is empty or too short; a warning when the reading order of a table page looks scrambled. See the spec for the CSV field set (including pilot, notes, and the page→PDF link fields).

**Blocked by:** None (can start immediately)

**Status:** done (pending review)

- [x] A valid small fake dataset passes validation
- [x] Wrong naming, a missing row, an orphan image, an unknown condition and wrong per-page counts each produce a message naming the file or row
- [x] Pages with an empty or too-short text layer give a warning
- [x] Every page yields normalized ground truth
- [x] Tests go only through the command-line entry point, using a small fake dataset (fake CSV + synthetic images + small PDF)

## Comments

- Implementation: `python -m eval.cli validate --csv … --images … --pdfs … [--min-chars N]` (`src/eval/cli.py`, `src/eval/dataset.py`), tests in `tests/test_validate.py` (20 cases, CLI only), fake data built in `tests/fakedata.py`.
- Decisions: the CSV page→PDF link fields are named `pdf_file` (file name in the PDF directory) and `pdf_page` (1-based); the "too short" text-layer threshold defaults to 100 characters (`--min-chars`); suspected scrambled table reading order = WER > 0.3 between the default pdftotext reading order and the `-layout` line order. Errors exit with code 1, warnings do not affect exit code 0, an unreadable CSV gives 2.
