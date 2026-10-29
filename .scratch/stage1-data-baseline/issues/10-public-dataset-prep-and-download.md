# 10: Manual items before downloading public datasets, and the download

**What to build:** Manual work. Go through the to-dos at the end of `docs/public-datasets-checklist.md` item by item, then download: (1) email icdar.smartdoc@gmail.com about the use (course project ECE 253, evaluating OCR preprocessing for phone-captured documents, with the "Used for" row of the checklist attached); (2) check the Zenodo 5293201 and Zenodo 1230218 pages for additional license terms; (3) open an issue in the RDD GitHub repository or contact the authors to confirm that it may be used for a course project; (4) check that the DOI of SmartDoc-QA corresponds to the paper; (5) download: SmartDoc Ch.1 `sampleDataset.tar.gz` (21 MB), only a portion of blur/lighting/perspective extracted from SmartDoc-QA, and only the test part of RDD. After downloading, record the original directory structure in the checklist for 11 to use.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [ ] Notification email sent, and a copy kept
- [ ] Licenses on both Zenodo pages verified item by item, with the results written back to the checklist
- [ ] RDD license asked about or confirmed; do not distribute images until confirmed
- [ ] Downloaded data placed under `data/public/`, with SmartDoc-QA containing only the needed subset
- [ ] The original directory structure of each dataset (folder hierarchy, file naming rules, location of annotation/transcription files) recorded in the checklist
- [ ] The certificate problem of the official site smartdoc.univ-lr.fr worked around (Zenodo is authoritative), and the authors' contact details verified

## Comments

- The authors' email comes from the stage 1 decisions list and could not be verified on the official site; see the checklist.
- The full SmartDoc-QA package is 13.7 GB; do not download all of it.
