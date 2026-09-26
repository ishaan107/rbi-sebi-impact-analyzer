"""
Module 8: Backend API
Exposes the multi-agent system as a FastAPI service.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.graph.build_graph import build_graph
from src.agents.orchestrator import initialize_state
from src.ingestion.document_store import load_pair, list_all_documents

app = FastAPI(title="RegTech Multi-Agent System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = build_graph()


class AnalyzeRequest(BaseModel):
    doc_topic: str  # e.g. "kyc" -> loads kyc_old.json / kyc_new.json
    query: str


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        old_doc, new_doc = load_pair(request.doc_topic)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No document pair found for topic '{request.doc_topic}'")

    initial_state = initialize_state(
        query=request.query,
        doc_id=new_doc["doc_id"],
        old_text=old_doc["raw_text"],
        new_text=new_doc["raw_text"],
    )
    # Use pre-condensed text (see src/ingestion/condenser.py) if available,
    # to stay within LLM provider token/rate limits for large documents.
    initial_state["old_condensed"] = old_doc.get("condensed_text")
    initial_state["new_condensed"] = new_doc.get("condensed_text")

    final_state = _graph.invoke(initial_state)

    return {
        "doc_id": final_state.get("doc_id"),
        "query_type": final_state.get("query_type"),
        "delta": final_state.get("delta"),
        "evidence": final_state.get("evidence"),
        "impact_assessment": final_state.get("impact_assessment"),
        "final_memo": final_state.get("final_memo"),
        "trace": final_state.get("trace"),
    }


@app.get("/circulars")
def get_circulars():
    return {"doc_ids": list_all_documents()}


@app.get("/health")
def health():
    return {"status": "ok"}
