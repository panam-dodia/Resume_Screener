import io
import pdfplumber


def extract_text(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given its raw bytes."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def extract_name_heuristic(text: str) -> str:
    """
    Best-effort name extraction from resume text.
    Takes the first non-empty line as the candidate name.
    This is used as a fallback when the AI-based extraction fails.
    """
    for line in text.splitlines():
        line = line.strip()
        if line and len(line) < 60:
            return line
    return "Unknown"
