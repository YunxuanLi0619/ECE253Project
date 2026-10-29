from .normalize import NORMALIZE_VERSION, normalize
from .metrics import Scores, score
from .groundtruth import pdf_ground_truth
from .ocr import OCR_CONFIG, ocr_image, tesseract_version

__all__ = [
    "NORMALIZE_VERSION", "normalize", "Scores", "score",
    "pdf_ground_truth", "OCR_CONFIG", "ocr_image", "tesseract_version",
]
