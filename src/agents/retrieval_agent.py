"""
Module 3: Retrieval Agent (RAG)
Given the Diff Agent's structured delta, retrieves ONLY the internal
policy sections relevant to each specific change -- not the whole
policy document. Compresses retrieved chunks into short evidence
summaries with citations before handing off. This compression step
is a deliberate context-engineering decision: downstream agents never
see raw policy text, only distilled evidence.
"""
from src.rag.vector_store import query_policy
from src.llm_client import generate

COMPRESSION_PROMPT_TEMPLATE = """Summarize the following internal policy
excerpt in 1-2 sentences, focused specifically on its relevance to this
regulatory change topic: "{topic}"

Policy excerpt:
{chunk_text}

Return only the summary, no preamble."""


def _compress_chunk(chunk_text: str, topic: str) -> str:
    prompt = COMPRESSION_PROMPT_TEMPLATE.format(topic=topic, chunk_text=chunk_text)
    return generate(prompt).strip()


def run_retrieval_agent(doc_id: str, delta: dict, top_k: int = 4) -> dict:
    """
    For each change in the delta, retrieve relevant policy chunks and
    compress them into an evidence summary with citation.
    """
    evidence_list = []

    for change in delta.get("changes", []):
        topic = change["topic"]
        query = f"{topic}: {change.get('new_text_summary') or change.get('old_text_summary') or ''}"

        retrieved_chunks = query_policy(query, top_k=top_k)

        if not retrieved_chunks:
            evidence_list.append({
                "change_topic": topic,
                "matched_policy_section": None,
                "evidence_summary": None,
                "citation": None,
                "policy_gap": True,
            })
            continue

        # Take the single best match, compress it (context minimization)
        best_match = retrieved_chunks[0]
        summary = _compress_chunk(best_match["text"], topic)

        evidence_list.append({
            "change_topic": topic,
            "matched_policy_section": best_match["metadata"].get("source", "unknown"),
            "evidence_summary": summary,
            "citation": f"{best_match['metadata'].get('source', 'unknown')}, chunk {best_match['metadata'].get('chunk_index')}",
            "policy_gap": False,
        })

    return {"doc_id": doc_id, "evidence": evidence_list}


if __name__ == "__main__":
    # Manual smoke test -- requires vector store already indexed
    sample_delta = {
        "doc_id": "RBI_KYC_2023",
        "changes": [
            {"topic": "video KYC eligibility", "new_text_summary": "expanded eligibility criteria"}
        ],
    }
    print(run_retrieval_agent("RBI_KYC_2023", sample_delta))
