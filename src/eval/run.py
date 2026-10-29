"""Single-image evaluation: python -m eval.run <image> <gt.txt | doc.pdf> [--page N]  ->  JSON on stdout."""
import argparse
import json
from pathlib import Path

from .groundtruth import pdf_ground_truth
from .metrics import score
from .normalize import NORMALIZE_VERSION, normalize
from .ocr import OCR_CONFIG, ocr_image, tesseract_version


def evaluate_image(image: str, gt_text: str) -> dict:
    hyp = normalize(ocr_image(image))
    ref = normalize(gt_text)
    return {
        "image": str(image),
        "tesseract": tesseract_version(),
        "ocr_config": OCR_CONFIG,
        "normalize_version": NORMALIZE_VERSION,
        **score(ref, hyp).to_dict(),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image")
    ap.add_argument("gt", help="ground-truth .txt (raw) or .pdf (text layer via pdftotext)")
    ap.add_argument("--page", type=int, help="PDF page, 1-based (default: whole PDF)")
    args = ap.parse_args()
    if Path(args.gt).suffix.lower() == ".pdf":
        gt_text = pdf_ground_truth(args.gt, args.page)
    else:
        gt_text = Path(args.gt).read_text(encoding="utf-8")
    result = evaluate_image(args.image, gt_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
