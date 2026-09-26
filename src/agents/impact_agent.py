"""
Module 4: Impact Agent
Receives ONLY the Diff Agent's delta summaries + Retrieval Agent's
evidence summaries -- never raw circular or raw policy text. This
enforced scoping is a core context-engineering decision: the Impact
Agent's job is reasoning, not re-reading source documents.

Also assigns a confidence score per assessment. The Orchestrator uses
this to decide whether to re-route back to the Retrieval Agent with a
refined query before proceeding to the Writer Agent.
"""
from src.llm_client import generate_json

IMPACT_SYSTEM_PROMPT = """You are a compliance risk analyst. Given a
regulatory change and the matching internal policy evidence (if any),
assess how significantly the organization's processes/policies are
impacted. Be conservative: if evidence is missing or weak, say so and
lower your confidence rather than guessing."""

IMPACT_USER_PROMPT_TEMPLATE = """Regulatory change:
Topic: {topic}
Change type: {change_type}
Old: {old_summary}
New: {new_summary}
Significance (per regulator): {significance}

Matched internal policy evidence:
{evidence_summary}
Policy gap (no matching policy found): {policy_gap}

Return JSON in this exact format:
{{
  "change_topic": "{topic}",
  "impact_level": "high" | "medium" | "low" | "none",
  "reasoning": "1-3 sentence explanation",
  "confidence": 0.0-1.0,
  "policy_gap": true | false
}}
"""


def run_impact_agent(doc_id: str, delta: dict, evidence: dict) -> dict:
    """
    Pairs each delta change with its corresponding evidence entry
    (matched by topic) and produces an impact assessment.
    """
    evidence_by_topic = {e["change_topic"]: e for e in evidence.get("evidence", [])}
    assessments = []

    for change in delta.get("changes", []):
        topic = change["topic"]
        ev = evidence_by_topic.get(topic, {})

        prompt = IMPACT_USER_PROMPT_TEMPLATE.format(
            topic=topic,
            change_type=change.get("change_type"),
            old_summary=change.get("old_text_summary") or "N/A",
            new_summary=change.get("new_text_summary") or "N/A",
            significance=change.get("significance"),
            evidence_summary=ev.get("evidence_summary") or "No matching policy section found.",
            policy_gap=ev.get("policy_gap", True),
        )
        result = generate_json(prompt, system=IMPACT_SYSTEM_PROMPT)
        assessments.append(result)

    avg_confidence = (
        sum(a.get("confidence", 0) for a in assessments) / len(assessments)
        if assessments else 0.0
    )

    return {
        "doc_id": doc_id,
        "impact_assessment": assessments,
        "overall_confidence": avg_confidence,
    }
