# Fixed OCR configuration and CER/WER convention throughout

All CER/WER values use the same fixed evaluation protocol, unchanged midway; otherwise earlier and later results are not comparable. OCR: Tesseract 5.x installed via brew, default tessdata, `eng` only, `--psm 3 --oem 1` (automatic layout analysis + LSTM), no `-c` parameters, no DPI override. PSM 3 was chosen over 6 because it is closest to real use, and the damage that perspective/shadow do to layout analysis is exactly what we want to quantify; the cost is that the reading order of multi-column layouts also affects CER.

Normalization (one shared function for the OCR output and the ground truth): NFKC, collapse all whitespace into single spaces and strip the ends, keep case and punctuation, do not join hyphenated line-break words. N in CER includes spaces, WER splits words on whitespace, and CER is not clipped to 1. Aggregation: each image's CER is the raw data; the condition and document-type tables use the macro-average as the main figure, with the micro-average (total errors / total characters) in an appendix table; a per-page distribution is also plotted.

Ground truth is extracted with poppler's `pdftotext` (without `-layout`) from PDFs that have a text layer, then passed through the same normalization function.

The header of every evaluation output file records `tesseract --version`, PSM/OEM and the normalization version.

## Considered Options

- PSM 6 (single uniform block of text): more stable, but scrambles multi-column paper pages; not adopted.
- Lowercasing, stripping punctuation: would mask real recognition errors; not adopted.
- `tessdata_best`: more accurate but slower, and it may discriminate less between degraded images; not adopted.
