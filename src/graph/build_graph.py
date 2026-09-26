"""
Module 6 (support): LangGraph wiring.
Defines the multi-agent graph. The Orchestrator makes exactly ONE routing
decision (right after the Diff Agent runs): does the user's query need
just the diff, or the full Retrieval -> Impact -> Writer chain? Each
agent node reads only what it needs from state and writes back only its
own output field -- the graph structure IS the enforcement mechanism
for context scoping.
"""
from langgraph.graph import StateGraph, END
from src.graph.state import TaskState
from src.agents.diff_agent import run_diff_agent
from src.agents.retrieval_agent import run_retrieval_agent
from src.agents.impact_agent import run_impact_agent
from src.agents.writer_agent import run_writer_agent
from src.agents.orchestrator import route_after_diff


def diff_node(state: TaskState) -> dict:
    old_text = state.get("old_condensed") or state["old_text"]
    new_text = state.get("new_condensed") or state["new_text"]
    print(f"[DEBUG] old_text length: {len(old_text)}, new_text length: {len(new_text)}", flush=True)
    print(f"[DEBUG] state has old_condensed key: {'old_condensed' in state}, value is None: {state.get('old_condensed') is None}", flush=True)
    delta = run_diff_agent(state["doc_id"], old_text, new_text)
    state.setdefault("trace", []).append({"node": "diff_agent", "note": f"{len(delta.get('changes', []))} changes found"})
    return {"delta": delta}


def retrieval_node(state: TaskState) -> dict:
    evidence = run_retrieval_agent(state["doc_id"], state["delta"])
    state.setdefault("trace", []).append({"node": "retrieval_agent", "note": f"{len(evidence.get('evidence', []))} evidence items"})
    return {"evidence": evidence}


def impact_node(state: TaskState) -> dict:
    impact = run_impact_agent(state["doc_id"], state["delta"], state["evidence"])
    state.setdefault("trace", []).append({"node": "impact_agent", "note": f"confidence={impact.get('overall_confidence'):.2f}"})
    return {"impact_assessment": impact}


def writer_node(state: TaskState) -> dict:
    memo = run_writer_agent(
        state["doc_id"],
        state["delta"],
        state.get("impact_assessment", {"impact_assessment": []}),
    )
    state.setdefault("trace", []).append({"node": "writer_agent", "note": "memo generated"})
    return {"final_memo": memo}


def build_graph():
    graph = StateGraph(TaskState)

    graph.add_node("diff", diff_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("impact", impact_node)
    graph.add_node("writer", writer_node)

    graph.set_entry_point("diff")

    graph.add_conditional_edges(
        "diff",
        route_after_diff,
        {"retrieval": "retrieval", "writer": "writer"},
    )
    graph.add_edge("retrieval", "impact")
    graph.add_edge("impact", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    print(app.get_graph().draw_ascii())
