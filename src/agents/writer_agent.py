"""
Module 5: Writer Agent
Receives only the final distilled outputs of Diff, Retrieval, and
Impact agents -- small, structured, already-reasoned-over content.
Never touches raw circular or raw policy text. Synthesizes the final
human-readable, cited compliance memo.
"""
from src.llm_client import generate

WRITER_SYSTEM_PROMPT = """You are a compliance officer writing a clear,
professional memo for internal stakeholders summarizing a regulatory
change and its business impact. Be concise, cite sources, and
explicitly flag any policy gaps or low-confidence assessments."""

WRITER_USER_PROMPT_TEMPLATE = """Write a compliance memo based on the
following structured analysis.

Document: {doc_id}

Changes identified:
{changes_block}

Impact assessments:
{impact_block}

Structure the memo with:
1. Executive summary (2-3 sentences)
2. Per-change breakdown (topic, what changed, impact level, reasoning, citation)
3. Flagged policy gaps (if any)
4. Recommended next actions
"""


def _format_changes(delta: dict) -> str:
    lines = []
    for c in delta.get("changes", []):
        lines.append(
            f"- [{c.get('change_type')}] {c.get('topic')} "
            f"(significance: {c.get('significance')}): "
            f"OLD: {c.get('old_text_summary')} | NEW: {c.get('new_text_summary')}"
        )
    return "\n".join(lines)


def _format_impact(impact: dict) -> str:
    lines = []
    for a in impact.get("impact_assessment", []):
        lines.append(
            f"- {a.get('change_topic')}: impact={a.get('impact_level')} "
            f"(confidence={a.get('confidence')}), gap={a.get('policy_gap')} "
            f"-- {a.get('reasoning')}"
        )
    return "\n".join(lines)


def run_writer_agent(doc_id: str, delta: dict, impact: dict) -> str:
    prompt = WRITER_USER_PROMPT_TEMPLATE.format(
        doc_id=doc_id,
        changes_block=_format_changes(delta),
        impact_block=_format_impact(impact),
    )
    return generate(prompt, system=WRITER_SYSTEM_PROMPT)
