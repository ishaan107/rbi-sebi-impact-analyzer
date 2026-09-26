"""
Module 6: Orchestrator Agent
The coordination brain of the system:
  1. Parses user intent -> decides query_type
  2. Builds the initial task plan (which nodes to visit)
  3. Owns the shared TaskState
  4. On low Impact Agent confidence, re-routes back to Retrieval Agent
     with a broadened query (bounded by MAX_RETRIES) instead of just
     proceeding with a weak answer
  5. Logs every routing decision to state["trace"] for later inspection
"""
from src.llm_client import generate_json
from src.config import IMPACT_CONFIDENCE_THRESHOLD, MAX_RETRIES

INTENT_SYSTEM_PROMPT = """You classify user queries about regulatory
circulars into one of two types:
- "diff_only": user just wants to know what changed (no business impact needed)
- "full_analysis": user wants to know what changed AND how it affects the business
Return JSON: {"query_type": "diff_only" | "full_analysis"}"""


def classify_intent(query: str) -> str:
    prompt = f'User query: "{query}"'
    result = generate_json(prompt, system=INTENT_SYSTEM_PROMPT)
    return result.get("query_type", "full_analysis")


def _log_trace(state: dict, node: str, note: str = ""):
    state.setdefault("trace", [])
    state["trace"].append({"node": node, "note": note})


def route_after_diff(state: dict) -> str:
    """After Diff Agent runs: skip straight to Writer if diff_only query."""
    _log_trace(state, "orchestrator", f"routing after diff, query_type={state.get('query_type')}")
    if state.get("query_type") == "diff_only":
        return "writer"
    return "retrieval"


def route_after_impact(state: dict) -> str:
    """
    After Impact Agent runs: check confidence. If too low and retries
    remain, loop back to Retrieval Agent with a broadened query instead
    of handing a weak assessment straight to the Writer.
    """
    confidence = state.get("impact_assessment", {}).get("overall_confidence", 1.0)
    retry_count = state.get("retry_count", 0)

    _log_trace(
        state, "orchestrator",
        f"post-impact confidence={confidence:.2f}, retry_count={retry_count}"
    )

    if confidence < IMPACT_CONFIDENCE_THRESHOLD and retry_count < MAX_RETRIES:
        state["retry_count"] = retry_count + 1
        _log_trace(state, "orchestrator", "confidence below threshold -> re-routing to retrieval")
        return "retrieval"

    return "writer"


def initialize_state(query: str, doc_id: str, old_text: str, new_text: str) -> dict:
    """Entry point: builds the initial TaskState from a raw user request."""
    query_type = classify_intent(query)
    state = {
        "query": query,
        "doc_id": doc_id,
        "query_type": query_type,
        "old_text": old_text,
        "new_text": new_text,
        "retry_count": 0,
        "trace": [],
    }
    _log_trace(state, "orchestrator", f"intent classified as {query_type}")
    return state
