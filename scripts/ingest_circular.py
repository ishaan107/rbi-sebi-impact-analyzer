"""
One-off script: parse a circular PDF and save it into the document store.

Usage:
  python scripts/ingest_circular.py \\
      --pdf data/raw/rbi_kyc_2023.pdf \\
      --topic kyc --version old \\
      --title "Master Direction - KYC (2023)" \\
      --issuer RBI --category KYC --date 2023-01-10 \\
      --source_url "https://rbi.org.in/..."
"""
import argparse
from src.ingestion.pdf_parser import parse_circular_pdf
from src.ingestion.document_store import save_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--topic", required=True, help="shared topic prefix, e.g. 'kyc'")
    parser.add_argument("--version", required=True, choices=["old", "new"])
    parser.add_argument("--title", required=True)
    parser.add_argument("--issuer", required=True, choices=["RBI", "SEBI"])
    parser.add_argument("--category", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--source_url", default="")
    args = parser.parse_args()

    raw_text = parse_circular_pdf(args.pdf)

    doc = {
        "doc_id": f"{args.topic}_{args.version}",
        "title": args.title,
        "issuer": args.issuer,
        "category": args.category,
        "version": args.version,
        "date": args.date,
        "raw_text": raw_text,
        "source_url": args.source_url,
    }

    path = save_document(doc)
    print(f"Saved parsed circular to {path} ({len(raw_text)} chars extracted)")


if __name__ == "__main__":
    main()
