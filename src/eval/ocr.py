"""Fixed Tesseract configuration (ADR-0001). Do not change mid-project."""
import subprocess

PSM = 3
OEM = 1
LANG = "eng"
OCR_CONFIG = {"psm": PSM, "oem": OEM, "lang": LANG}


def tesseract_version() -> str:
    out = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True)
    return (out.stdout or out.stderr).splitlines()[0].strip()


def ocr_image(path: str) -> str:
    out = subprocess.run(
        ["tesseract", str(path), "stdout", "-l", LANG, "--psm", str(PSM), "--oem", str(OEM)],
        capture_output=True, text=True, check=True,
    )
    return out.stdout
