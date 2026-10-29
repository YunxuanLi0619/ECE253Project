# Public Dataset Checklist

Per ADR-0002, results on public datasets get one table per reference source (`python -m eval.cli public`). Information checked on 2026-10-01 (Zenodo / GitHub pages); **the manual to-dos before downloading are at the end and are not yet done.**

| | SmartDoc-QA | SmartDoc 2015 Ch.1 sample | RDD |
|---|---|---|---|
| URL | https://zenodo.org/record/5293201 | https://zenodo.org/records/1230218 | https://github.com/hyyh1314/RDD (data is in the [Google Drive folder](https://drive.google.com/drive/folders/1nS-p9qKCsFjOFyzq5q2m-Dq-PJVmLfNc?usp=sharing) given in its README) |
| How to download | Direct download of `Dataset SmartDoc-QA.zip` from Zenodo; extract only the needed subset | Download `sampleDataset.tar.gz` from Zenodo (not `testDataset.tar.gz`) | Download from Google Drive; the test part is enough |
| Size | 13.7 GB (about 4260 images, 30 document pages) | 21.2 MB (sample); the 1.5 GB test package is not downloaded | 4914 pairs (4371 train / 545 test); size not stated on the page |
| License | CC BY 4.0 | CC BY 4.0 | **Not stated** (no license terms in the README) |
| Citation | Nayef, Luqman, Prum, Eskenazi, Chazalon, Ogier. *SmartDoc-QA: A Dataset for Quality Assessment of Smartphone Captured Document Images – Single and Multiple Distortions.* CBDAR 2015 | Burie et al. *ICDAR2015 Competition on Smartphone Document Capture and OCR (SmartDoc).* ICDAR 2015; dataset: Chazalon & Rusiñol, Zenodo, doi:10.5281/zenodo.1230218 | Zhang, He, Zhang, Liu, Zhang, Xiao. *Document Image Shadow Removal Guided by Color-Aware Background.* CVPR 2023 |
| Has text? | **Yes**: human-transcribed text, plus the dataset's own OCR results and capture parameters | No: only document-quadrilateral annotations | No: only paired "with shadow / without shadow" images |
| Reference source | Human transcription | — (no CER computed) | Pseudo ground truth (OCR of the same scene's shadow-free image) |
| Used for | A portion each of blur / lighting / perspective, grouped by its three document classes (modern documents, old administrative letters, receipts); report CER/WER | Only the **corner-detection success rate** of perspective rectification | Relative improvement of shadow removal (relative only, not treated as true accuracy) |
| Result table | `public_smartdoc_qa.md`, header "reference: human transcription" | Not covered by the `public` command (the corner evaluation of stage 3) | `public_rdd.md`, header "reference: pseudo ground truth, relative improvement only" |

DocUNet and Hradiš are not used for now; there is no suitable public set of real blurred documents, so self-collected + synthetic blur is used instead.

## Manual to-dos before downloading

- [ ] **Tell the SmartDoc authors about the intended use**: email icdar.smartdoc@gmail.com (address from the stage 1 decisions list; the authors ask users to notify them), stating that this is a course project (ECE 253) evaluating OCR preprocessing for phone-captured documents, and attach the "Used for" row of the table above. The Zenodo page also requires attribution under CC BY.
- [ ] **Re-verify the licenses against the original pages**: the licenses in this table come from the summaries on the Zenodo / GitHub pages; before downloading, open Zenodo 5293201 and Zenodo 1230218 again and confirm each item (including any additional terms).
- [ ] **RDD license is not stated**: before downloading, open an issue in the GitHub repository or contact the authors to confirm that it may be used for a course project; until confirmed, use it only for in-course evaluation and do not redistribute the images.
- [ ] Check that the DOI listed on the SmartDoc-QA Zenodo page (10.1109/ICDAR.2015.7333960) corresponds to the CBDAR paper; cite according to the original page.
- [ ] The HTTPS certificate of the official site smartdoc.univ-lr.fr does not match (error when visited on 2026-10-01); re-check the authors' contact details and the dataset description on the official page or on Zenodo.
- [ ] Cite the papers of the three datasets above in the report, and state that only a subset of SmartDoc-QA was used.

## Directory format for the `public` command

```
<root>/smartdoc_qa/manifest.csv   columns: filename, page_id, doc_class, distortion, reference
                  images/<filename>
                  transcriptions/<reference>     # human-transcribed text of that page
<root>/rdd/manifest.csv           columns: filename, page_id, condition  (clean | shadow; page_id is the scene number)
          images/<filename>
```

`python -m eval.cli public --root <root> --out <out>` writes one `public_<dataset>.md/.json` for each dataset that exists; `--ocr-texts FILE` (`<dataset>/<filename>` → raw OCR text) can replace the OCR. The manifest has to be put together by hand from the downloaded subset (the original directory structure of each dataset has not been checked and has not yet been aligned with this format).
