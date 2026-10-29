"""Ground truth from a PDF text layer (ADR-0001): poppler pdftotext, no -layout."""
import subprocess


def pdf_ground_truth(pdf: str, page: int | None = None) -> str:
    """Raw (unnormalized) text of the PDF, or of one 1-based page."""
    cmd = ["pdftotext"]
    if page is not None:
        cmd += ["-f", str(page), "-l", str(page)]
    out = subprocess.run(cmd + [str(pdf), "-"], capture_output=True, text=True, check=True)
    return out.stdout
