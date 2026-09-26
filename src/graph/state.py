"""
Module 6 (support): Shared Task State.
This is THE central context-engineering artifact of the project.
Every agent reads/writes only the fields it needs from this state --
never the full conversation or full source documents. Document this
explicitly in your report with a field-by-field justification.
"""
from typing import TypedDict, Optional


class TaskState(TypedDict, total=False):
    # --- input ---
    query: str
    doc_id: str
    query_type: str  # "diff_only" | "full_analysis"

    # --- raw source refs (loaded once, not re-passed to every agent) ---
    old_text: str
    new_text: str

    # --- pre-condensed text for large documents (see condenser.py /
    # local_reducer.py) -- used instead of old_text/new_text when present,
    # to stay within LLM provider token/rate limits ---
    old_condensed: Optional[str]
    new_condensed: Optional[str]

    # --- agent outputs (distilled, structured) ---
    delta: Optional[dict]
    evidence: Optional[dict]
    impact_assessment: Optional[dict]
    final_memo: Optional[str]

    # --- orchestration control ---
    next_node: Optional[str]
    trace: list  # append-only log of {node, input_keys, output_keys} for demo/grading
