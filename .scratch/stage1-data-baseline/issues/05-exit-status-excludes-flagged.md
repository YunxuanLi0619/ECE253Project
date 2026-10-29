# 05: Align the stage exit verdict with the main table convention (exclude ⚠ types)

**What to build:** Currently the "Overall" column of the `report` main table excludes ⚠ types whose clean-baseline CER > 20% (such as receipts), but the stage exit status is computed over "all pages". In a rehearsal (36 pages of simulated data, receipt pages with clean CER 384%), the receipts pulled the mean gap of shadow down to +3.0 percentage points and caused a wrong FAIL; without the receipts, shadow is more than 40 percentage points above the clean baseline. Change it so that: the stage exit status is computed only over pages of non-⚠ types (the pilot verdict is unchanged, see the comments); ⚠ types get their own line listing each condition's gap to its clean baseline for separate discussion, without taking part in the pass/fail conclusion. The report states which types were excluded this time.

**Blocked by:** 03

**Status:** done (pending review)

- [x] Crafted data: when a type has clean CER > 20% and drags down the mean gap, the stage exit status no longer FAILs because of it
- [x] The report states the excluded types and separately lists the gap of each condition's CER to the clean baseline for these types
- [x] When there are no ⚠ types, the result is exactly the same as now (regression)
- [x] If a defect has too few effective pages after exclusion (e.g. < 3 pages), the report notes "too few pages, verdict for reference only"
- [x] Tests go only through the command-line entry point, using `--precomputed` to craft CERs

## Comments

- Source: found on 2026-10-02 when running `report` on 36 pages / 432 simulated images made from a local paper PDF (see the conversation); the verdict convention was inconsistent with the main table.
- To be confirmed by you: story 26 of the spec only says receipts are discussed separately and not folded into the totals, and does not say whether they are also excluded from the exit verdict; this ticket was written as "exclude them too", change it back if you disagree.
- Implementation: `src/eval/report.py` (`build_summary` computes `stage_exit` only over non-⚠ types; added `flagged_verdicts`, `few_page_conditions`, `MIN_PAGES_FOR_VERDICT = 3`), `src/eval/cli.py` (the title changed to "excluding flagged types", and it prints the gaps of the excluded types and the too-few-pages note); the 5 tests at the end of `tests/test_report.py` go through the command line only.
- **One difference from the original ticket text**: the original said "both the stage exit status and the pilot verdict exclude ⚠ types", but the implementation excludes them only from the stage exit status. Reason: story 27 of the spec has a dedicated ≥ 1.5× rule for "pages whose baseline is already poor", so the pilot verdict already accommodates such pages; excluding them would drop the receipt pages from the pilot entirely (the existing test `test_poor_baseline_page_needs_one_and_a_half_times` fails because of this). The pilot verdict behavior stays as it was.
- The gaps of the excluded types are listed separately (the "Excluded ⚠ types" section of the report and the terminal output) and do not take part in the pass/fail.
- The current directory is not a git repository, so nothing was committed and the diff-based /code-review was not run.
