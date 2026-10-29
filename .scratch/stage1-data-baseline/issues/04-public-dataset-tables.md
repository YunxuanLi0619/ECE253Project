No

# 04: Public dataset tables and checklist

**What to build:** Evaluation results of public datasets get one table per reference source (ADR-0002): SmartDoc-QA uses human transcription, grouped by its own three document classes; RDD uses pseudo ground truth, with the header stating that it reflects only relative improvement. All reference texts still pass through the same normalization. Also add a checklist document that records, dataset by dataset, the URL, download method, size, license, citation, whether it has text, and intended use; the manual items before downloading (telling the SmartDoc authors about the use, re-verifying licenses against the original pages) are written in the checklist.

**Blocked by:** 03

**Status:** done (pending review)

- [X] Results from the three reference sources do not appear in the same table
- [X] The SmartDoc-QA table is grouped by its three document classes, with the header stating "human transcription"
- [X] The RDD table header states "pseudo ground truth, relative improvement only"
- [X] The checklist covers SmartDoc-QA, the SmartDoc Ch.1 sample and RDD, and lists the manual to-dos before downloading
- [X] Tests use a small fake public-dataset directory and verify the table splitting through the command-line entry point

## Comments

Implementation done: `python -m eval.cli public --root PUBLIC_DIR --out OUT_DIR [--ocr-texts FILE]` (`src/eval/public.py`, `cli.py`), tests in `tests/test_public.py` (17 cases, via the CLI; the fake directory is built in `tests/fakedata.py::FakePublic`), checklist in `docs/public-datasets-checklist.md`.

- Decision: I chose the public-dataset directory format (described at the end of the checklist) because the spec does not define one: `<root>/smartdoc_qa/` (manifest + images + transcriptions) and `<root>/rdd/` (manifest + images, condition is clean/shadow). Each dataset writes its own `public_<name>.md/.json`, so results from different reference sources are physically never in the same file.
- RDD: the CER of a shadow image is computed against the OCR (passed through normalize) of the clean image of the same scene; the clean image itself is not scored. SmartDoc-QA is split into columns by doc_class and rows by distortion, and cells work as in the self-collected report (page-level means, n, median, interval only for n ≥ 5).
- OCR results are cached by image sha256 in `public_ocr_cache.json` (invalidated when the header changes).
- The SmartDoc authors' email in the checklist comes from the stage 1 decisions list and could not be verified on the official site (its HTTPS certificate errors); the manual to-dos are all still open.
- The current directory is not a git repository, so nothing was committed and the diff-based /code-review could not be used.
