# Stage Opening Prompts

At the start of each stage, copy and send the matching prompt. Stage 0 attaches the PDF; afterwards the key content has been distilled into `CONTEXT.md`, so the prompts no longer attach the PDF; add `@"ECE 253 Course Project Plan - OCR Preprocessing for Phone-Captured Documents.pdf"` manually when the original text needs checking.

Flow of each stage: `/grill-with-docs` → (optional) `/to-spec` → `/to-tickets` → `/implement` → accept against the completion criteria.

Hard milestones: 10/6 team form · 11/3 proposal · 11/10 midterm sign-up and checkpoint · 11/18–20 midterm presentation · 11/24 final presentation sign-up · 12/5–7 final presentation · 12/11 report

---

## Stage 0: Project setup and environment (until 10/6)

```
/grill-with-docs @"ECE 253 Course Project Plan - OCR Preprocessing for Phone-Captured Documents.pdf" Stage 0: project setup and environment. Environment setup for Python/OpenCV/Tesseract/jiwer, the convention of the CER/WER evaluation script (whether to normalize text, how to handle whitespace and punctuation, which Tesseract version and PSM parameters to fix), the project directory structure, the glossary (CER, WER, clean baseline, combo set, P0–P6, etc.)
```

**Completion criteria**: the evaluation script runs through on one test image; the email confirming working solo has been sent.

---

## Stage 1: Data collection and baseline (until 10/20)

```
/grill-with-docs Stage 1: data collection and baseline. Pin down in particular: the selection of 30–40 PDF pages (mix of paper pages/book pages/receipts/tables), the capture protocol (conditions for the 12 shots per page and the division of labor between phones), the file naming doc-id_condition_seq.jpg and the metadata CSV fields, the by-page tuning/test split (fixed random seed), the pass criteria for the small pilot batch, the checklist for public datasets (download method and license), and the convention of reporting the baseline evaluation separately by document type
```

**Completion criteria**: about 360 images + metadata CSV; the baseline CER of the blur, shadow and perspective conditions is clearly above the clean baseline, otherwise reshoot.

---

## Stage 2: Preliminary experiments and proposal (until 11/3)

```
/grill-with-docs Stage 2: preliminary experiments and proposal. Pin down in particular: the unified interface of the three simplest prototypes (Wiener, background division + Sauvola, contour corners + homography) (inputs/outputs, parameters, save paths), how to validate Wiener first on synthetic data with a known PSF, the generation pipeline of the synthetic data (shadow first, then perspective, finally blur), the structure of the proposal and the literature to cite, and the criterion for prototype success (CER drops on at least some images)
```

**Completion criteria**: all three prototypes lower the CER of at least some images; submit the proposal before 11:59 pm on 11/3.

---

## Stage 3: Primary methods and midterm presentation prep (until the 11/10 checkpoint)

```
/grill-with-docs Stage 3: primary methods. Pin down in particular: refinements to the perspective and shadow primary methods (handling of corner-detection failures, kernel size and threshold window), the implementation of blur PSF estimation (spectral dark stripes/cepstrum) and the upper-bound comparison (known PSF), the format of the "with vs. without preprocessing" CER comparison table, and the judgment at the 11/10 checkpoint and the triggers for cutting scope (per the cut order in section 8 of the PDF)
```

**Completion criteria**: each of the three defects has a "with vs. without preprocessing" CER comparison, which may be rough; sign up for the midterm presentation before 11/10. If not met, cut scope according to the cut order.

---

## Stage 4: Midterm presentation (11/18–20)

Mostly execution; a full grill is not needed. Short version:

```
/grill-me Stage 4: midterm presentation. Help me organize the slide structure (problem, method, preliminary results, next steps) and decide which charts best show that "preprocessing works"
```

**Completion criteria**: slides uploaded before 11:59 pm on 11/20; a list of follow-up changes drawn up from the feedback of the instructor and classmates.

---

## Stage 5: Comparison methods, improvements and combination experiments (until 12/5)

```
/grill-with-docs Stage 5: comparison methods, improvements and combination experiments. Pin down in particular: the implementation boundary of the second traditional method (Richardson-Lucy, homomorphic filtering + Retinex, Hough + RANSAC), the adaptive improvements for the self-collected data (K and kernel size by stroke width/line height, corner fallback strategy), the range of the parameter sweeps and the curve format, parameter logging for the synthetic data, the experiment design of the P0–P6 order ablation (inputs, outputs and statistics per group), and the outline of the report's method and data sections
```

**Completion criteria**: every row of the experiment matrix has numbers; sign up for the final presentation before 11/24.

---

## Stage 6: Final presentation and report (until 12/11)

Mostly execution. Short version:

```
/grill-me Stage 6: final presentation and report. Help me follow the handout's chapter order, work out the source material and gaps for each chapter of the report, and ask how to write the analysis when the experimental results disagree with the hypothesis
```

**Completion criteria**: final slides uploaded before 11:59 pm on 12/7; final report submitted before 11:59 pm on 12/11; contribution field says 100%.
