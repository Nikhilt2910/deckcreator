from pathlib import Path

from pypdf import PdfReader


def load_reference_context(reference_path: Path | None) -> dict[str, str]:
    if reference_path is None:
        return {
            "reference_type": "none",
            "reference_text": "",
        }
    if reference_path.suffix.lower() == ".pdf":
        return {
            "reference_type": "pdf",
            "reference_text": _extract_pdf_text(reference_path),
        }
    return {
        "reference_type": "pptx",
        "reference_text": "",
    }


def _extract_pdf_text(reference_path: Path) -> str:
    reader = PdfReader(str(reference_path))
    pages: list[str] = []
    for page in reader.pages[:6]:
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(text)
    return "\n\n".join(pages)[:5000]
