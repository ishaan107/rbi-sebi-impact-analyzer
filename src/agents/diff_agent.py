"""
Module 2: Diff Agent
Compares old vs. new circular text and extracts a STRUCTURED delta.
This structured delta -- not the raw circular text -- is what gets
passed to every downstream agent. This is the first context-engineering
decision point in the pipeline.
"""
from src.llm_client import generate_json

# Hard safety cap (characters, ~4 chars/token rule of thumb) applied
# regardless of upstream condensing, so this agent NEVER exceeds
# provider rate limits even if a document slips through un-condensed.
MAX_OLD_TEXT_CHARS = 33000
MAX_NEW_TEXT_CHARS = 6000

DIFF_SYSTEM_PROMPT = """You are a regulatory compliance analyst specializing in
identifying substantive changes between two versions of a financial regulation.
You focus only on changes that affect obligations, eligibility, thresholds,
processes, or reporting requirements. Ignore purely stylistic/wording changes
that don't alter meaning."""

DIFF_USER_PROMPT_TEMPLATE = """Compare the OLD and NEW versions of this regulatory
circular. Identify every substantive change.

OLD VERSION:
{old_text}

NEW VERSION:
{new_text}

Return JSON in this exact format:
{{
  "doc_id": "{doc_id}",
  "changes": [
    {{
      "change_type": "added" | "removed" | "modified" | "clarified",
      "topic": "short topic label, e.g. 'video KYC eligibility'",
      "old_text_summary": "brief summary of what the old version said (or null if added)",
      "new_text_summary": "brief summary of what the new version says (or null if removed)",
      "significance": "high" | "medium" | "low"
    }}
  ]
}}
"""


def run_diff_agent(doc_id: str, old_text: str, new_text: str) -> dict:
    """
    Main entry point for the Diff Agent.
    Applies a hard safety-net truncation on top of any upstream
    condensing (condenser.py / local_reducer.py), guaranteeing this
    agent never sends a request that exceeds provider rate limits --
    truncation is logged explicitly, never silent.
    """
    if len(old_text) > MAX_OLD_TEXT_CHARS:
        print(f"[WARN] old_text truncated from {len(old_text)} to {MAX_OLD_TEXT_CHARS} chars for rate-limit safety")
        old_text = old_text[:MAX_OLD_TEXT_CHARS]
    if len(new_text) > MAX_NEW_TEXT_CHARS:
        print(f"[WARN] new_text truncated from {len(new_text)} to {MAX_NEW_TEXT_CHARS} chars for rate-limit safety")
        new_text = new_text[:MAX_NEW_TEXT_CHARS]

    prompt = DIFF_USER_PROMPT_TEMPLATE.format(
        old_text=old_text, new_text=new_text, doc_id=doc_id
    )
    result = generate_json(prompt, system=DIFF_SYSTEM_PROMPT)
    return result


def get_diff_text(doc: dict) -> str:
    """
    Prefer condensed_text if it exists (large docs pre-processed by
    src/ingestion/condenser.py to fit within LLM token/rate limits),
    otherwise fall back to raw_text for shorter documents.
    """
    return doc.get("condensed_text") or doc["raw_text"]


if __name__ == "__main__":
    # Manual smoke test once you have real doc pairs
    from src.ingestion.document_store import load_pair
    old_doc, new_doc = load_pair("kyc")
    delta = run_diff_agent(
        old_doc["doc_id"], get_diff_text(old_doc), get_diff_text(new_doc)
    )
    print(delta)
