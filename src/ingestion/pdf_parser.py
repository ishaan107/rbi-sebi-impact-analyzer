"""
Module 1: PDF Parser
Extracts and cleans raw text from RBI/SEBI circular PDFs.
"""
import re
import fitz  # pymupdf


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file, page by page."""
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def clean_text(raw_text: str) -> str:
    """
    Remove common PDF artifacts: repeated headers/footers, page numbers,
    excessive whitespace. Tune the regexes once you see real circular text.
    """
    text = re.sub(r"Page \d+ of \d+", "", raw_text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def parse_circular_pdf(pdf_path: str) -> str:
    """Convenience wrapper: extract + clean in one call."""
    raw = extract_text_from_pdf(pdf_path)
    return clean_text(raw)


if __name__ == "__main__":
    # Quick manual test once you have a real PDF in data/raw/
    import sys
    if len(sys.argv) > 1:
        print(parse_circular_pdf(sys.argv[1])[:1000])
