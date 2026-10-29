"""Text normalization shared by OCR output and ground truth (ADR-0001)."""
import re
import unicodedata

NORMALIZE_VERSION = "1"

_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """NFKC, collapse all whitespace to one space, strip. Case, punctuation and hyphens kept."""
    return _WS.sub(" ", unicodedata.normalize("NFKC", text)).strip()
