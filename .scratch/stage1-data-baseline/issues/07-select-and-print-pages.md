# 07: Select and print the 36 PDF pages

**What to build:** Manual work. Select 36 English PDF pages with a text layer: paper 12 (single-column 6, two-column 6), book page 10, table 8, receipt 6. Write the page list as a CSV (columns: page_id, doc_type, pdf_file, pdf_page) and put the PDFs in `data/pdf/`. Print these pages (on paper) for shooting. For every page, spot-check with `validate` or `python -m eval.run` that the text layer is extractable and of normal length. For table pages watch the pdftotext reading order; if a receipt has no text layer, swap the page or use pseudo ground truth (which must go in its own table, see ADR-0002).

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [ ] 36 pages selected, with type ratio 12/10/8/6 and 6 single-column and 6 two-column papers
- [ ] Page-list CSV written, with accurate `pdf_file` and `pdf_page`
- [ ] All PDFs placed in `data/pdf/`
- [ ] The text layer of every page is extractable, not empty text or obvious garbage
- [ ] No reading-order warnings on table pages; pages with warnings have been replaced
- [ ] The 36 pages are printed

## Comments

- The original plan document said 30 pages; in the stage 1 discussion you changed it to 36, and `docs/stage1-decisions.md` is authoritative.
- Pilot pages must come from the tuning set, and the tuning set is decided by `split`, so after selecting pages run `split` first (see 02) and then pick the pilot pages.
