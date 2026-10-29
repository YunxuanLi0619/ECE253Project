# OCR Preprocessing for Phone-Captured Documents

We study why casually phone-photographed documents are recognized poorly by OCR, apply image-processing methods to preprocess three kinds of defects, measure how much the recognition error rate drops, and finally study the preprocessing order when all three defects are stacked.

## Language

### Defects and capture

**Defect**:
A phenomenon during capture that makes OCR worse. This project studies only three: motion blur, shadow, perspective distortion.
_Avoid_: degradation (when referring to the phenomenon), problem

**Degradation model**:
A mathematical description of one defect (e.g. g = h * f + n, I = L × R, a homography).
_Avoid_: defect model

**Capture condition**:
A category in the capture protocol, 5 in total: clean, blur, shadow, perspective, combo. 12 shots per page (1+3+3+3+2).
_Avoid_: four conditions, scenario

**Clean baseline**:
The 1 real shot per page, taken flat and under even lighting, used as the reference.
_Avoid_: clean image, original image

**Digital original**:
The image rendered from the PDF; the starting point for synthetic data and the reference for PSNR/SSIM.
_Avoid_: clean baseline (the two are not the same thing)

**Combo set**:
The real shots of the combo condition, carrying tilt, shadow and motion blur at the same time (2 per page).
_Avoid_: synthetic combo

**Synthetic combo**:
A combo image synthesized from the digital original in imaging order (shadow first, then perspective, finally blur), with every stage's parameters known.
_Avoid_: combo set

### Data

**Page**:
One document page of the self-collected data and the smallest unit of the data split: all images of the same page go to either the tuning set or the test set.
_Avoid_: document (document refers to a class, such as paper page or receipt)

**ground truth**:
The original text extracted directly from a PDF with a text layer and, after normalization, used as the reference for CER/WER.
_Avoid_: annotation, hand-labeled text

**Pilot batch**:
A small batch shot before the formal shoot to check whether the defects hurt OCR enough. If it passes, it is kept and counted in the formal data, marked as pilot in the metadata.

**Pseudo ground truth**:
When no text layer can be extracted, the reference text obtained by running OCR on the lossless image of the same scene. The CER computed from it reflects only relative improvement, not true accuracy, and must go in its own table.
_Avoid_: ground truth (the two must not be called by the same name)

**Human transcription**:
The human-transcribed text that ships with a public dataset (SmartDoc-QA). It is normalized the same way and used as the reference, but its CER goes in a separate table and is not compared with the CER of the self-collected data in one table.

**Tuning set / Test set**:
Split by page: about one third of the pages are used for tuning, the rest for the final test.

### Methods and experiments

**Processing scheme**:
The numbered execution order of the three preprocessing steps, 7 in total. **P0** is the baseline (no processing); **P1–P6** are the order schemes, the 3! permutations of the deblur, deshadow and rectify steps. P1 is the order assumed to be optimal (deblur → rectify → deshadow).
_Avoid_: order group, P0 order

**Primary method / Comparison method**:
The two traditional methods for each defect: the primary method (e.g. Wiener, background division + Sauvola, contour corners + homography) and the comparison method (e.g. Richardson-Lucy, homomorphic filtering / Retinex, Hough + RANSAC). AI methods serve only as optional reference lines.

**Improved version**:
An adaptive modification of the primary method made for the self-collected data, compared against the original.
_Avoid_: optimized version

### Evaluation

**CER**:
Character error rate, (S + D + I) / N. S, D, I are the numbers of substituted, deleted and inserted characters; N is the number of characters in the ground truth.
_Avoid_: character-wrong rate

**WER**:
Word error rate; same algorithm as CER, with words as the unit.

**PSNR / SSIM**:
Auxiliary metrics of restored-image quality, computed only on synthetic data, because the real shots are not pixel-aligned with the clean baseline.

**Corner-detection success rate**:
In perspective rectification, the fraction of documents whose four corners are found correctly.

**PSM / OEM**:
Tesseract's page segmentation mode and OCR engine mode. Both are fixed throughout; see ADR-0001 for the values.
