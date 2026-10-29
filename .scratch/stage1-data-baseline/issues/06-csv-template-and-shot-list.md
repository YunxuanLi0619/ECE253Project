# 06: Metadata CSV template and shot-list generation

**What to build:** Given a "page list" (CSV with columns page_id, doc_type, pdf_file, pdf_page, optional phone_model), the command-line entry point generates two things: (1) a skeleton metadata CSV with 12 rows prefilled per page (1 clean + 3 blur + 3 shadow + 3 persp + 2 combo), with filename, page_id, doc_type, condition, seq, pdf_file, pdf_page already filled, blur_dir / angle_deg / shadow_type prefilled per protocol (blur is horizontal, vertical, diagonal; persp is 15/30/45; combo is hard shadow, soft shadow), phone_model prefilled as "phone A on odd pages, phone B on even pages, balanced within each type", and light, captured_at, resolution, notes to be filled in during the shoot; (2) a shot list grouped by page (markdown, with checkboxes, listing what to shoot for each image). Refuse to overwrite when an output file with the same name already exists. The generated skeleton should pass the naming and count checks of `validate` as is (except for missing images).

**Blocked by:** 01

**Status:** done (pending review)

- [x] Given a page list of 36 pages, output a 432-row CSV with 12 rows per page and names matching `p<page>_<condition>_<seq>.jpg`
- [x] The angle and shadow-type fields of blur / persp / combo are prefilled per protocol
- [x] Phone assignment follows the odd/even split, and the two phones are roughly balanced within each document type
- [x] The shot list is grouped by page with checkboxes, and pilot pages are marked separately
- [x] When an output file already exists, it is refused with an explanation
- [x] When the page list has a doc_type outside paper / book / table / receipt, or a missing pdf_page, an error points out which row
- [x] Tests go only through the command-line entry point, using a small fake page list

## Comments

- Corresponds to the stage 1 task "organize file names and metadata": 01 only validates and does not generate the CSV; this ticket supplies the generation half.
- Phone-balance details follow `docs/stage1-decisions.md`: A shoots odd pages, B shoots even pages, balanced within a type.
- Implementation: `python -m eval.cli template --pages pages.csv --csv meta.csv --checklist shotlist.md` (`src/eval/template.py`, `cli.py`), tests in `tests/test_template.py` (15 cases, command line only).
- Page-list columns: required `page_id, doc_type, pdf_file, pdf_page`; optional `phone_model` (overrides the default assignment if filled) and `pilot` (if true the skeleton has pilot=true and the list heading says "Pilot").
- Decisions: the `shadow_type` of the `shadow` condition is left empty because the protocol does not define a shadow type; only the combo set is prefilled with hard / soft. Phones default to A on odd pages and B on even pages; a WARNING is printed (without refusing) when the two phones differ by more than 1 page within a type. An existing output file is refused (exit code 1), and neither file is half-written.
- Errors in the page list are named by "line N" (unknown doc_type, empty pdf_file, non-positive-integer pdf_page, duplicate page id, missing column), and no file is written.
- The page list itself has to be put together by hand, and only exists after `07` is done; `light / captured_at / resolution / notes` and `split` are left empty, and `split` is still written by the `split` command.
- Once the images are in place, the skeleton passes `validate` as is (verified with 36 pages in the tests).
- The current directory is not a git repository, so nothing was committed and the diff-based /code-review was not run.
