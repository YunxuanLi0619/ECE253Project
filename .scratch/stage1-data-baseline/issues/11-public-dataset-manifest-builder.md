# 11: Script to organize public datasets into manifests

**What to build:** The `public` command of 04 requires a fixed directory format (`<root>/smartdoc_qa/manifest.csv + images/ + transcriptions/`, `<root>/rdd/manifest.csv + images/`), but the original structures of SmartDoc-QA and RDD have not yet been checked. After 10 finishes downloading, write an organizing entry point for each dataset: read the downloaded original directory, pick the subset by each dataset's own rules (SmartDoc-QA: a portion each of blur, lighting and perspective, keeping its three-document-class grouping; RDD: the test part, pairing with/without shadow by scene), generate `manifest.csv`, and arrange the images and transcription files as agreed. The organizing step does not modify the original images. Once generated, `python -m eval.cli public` should run through directly.

**Blocked by:** 04, 10

**Status:** needs-info

- [ ] The subset selection rule for SmartDoc-QA is settled (how many images per distortion, how to stratify) and recorded in the checklist
- [ ] The organized directory can be read by the `public` command, the SmartDoc-QA table is grouped by its three document classes, and the header says "human transcription"
- [ ] The RDD with/without-shadow pairing is correct, and the header says "pseudo ground truth, relative improvement only"
- [ ] The original download directory is not modified
- [ ] Tests verify the organized result with a small fake "original directory" (independent of the real download)

## Comments

- needs-info: the real directory structure after the 10 download is missing; writing it now would implement against guesses. After 10 is done and the structure is recorded, change the status to ready-for-agent.
- Another question for you to decide: how many images per distortion type to take from SmartDoc-QA. Suggest starting with a small subset to get the pipeline running.
