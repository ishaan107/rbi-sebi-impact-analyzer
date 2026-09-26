# RegTech Agent — RBI/SEBI Regulatory Change-Impact Multi-Agent System

A multi-agent system that reads old vs. amended RBI/SEBI circulars, extracts what actually changed, retrieves the relevant internal policy sections, reasons about business impact, and produces a cited compliance memo — automating work compliance teams at banks and NBFCs currently do by hand.

## The Problem

When RBI or SEBI issue new circulars or master directions that amend existing regulations, compliance teams have to manually figure out what changed and which internal policies or processes are affected. This process is slow, error-prone, and inconsistent across analysts.

## The Approach

Instead of a fixed pipeline, an **Orchestrator Agent** dynamically plans which agents to invoke based on the query — a simple "what changed?" question only needs the Diff Agent, while a full impact analysis chains Diff → Retrieval → Impact → Writer. Each agent receives a deliberately scoped, compressed subset of context rather than raw documents, and the Orchestrator re-routes automatically when the Impact Agent's confidence is too low.

This project demonstrates three things together:
- **Retrieval-Augmented Generation (RAG)** over regulatory and internal policy documents, with citations
- **Multi-agent orchestration**, with five distinct agents each owning a non-overlapping responsibility
- **Context engineering** — scoped state passing, compression before handoff, and confidence-based re-routing instead of a static pipeline

## Architecture

```
                     User Query (API/Frontend)
                              │
                    ┌─────────▼─────────┐
                    │  Orchestrator      │
                    │  Agent             │
                    └─────────┬─────────┘
        ┌────────────┬────────┴────────┬────────────┐
        ▼            ▼                 ▼             ▼
   Diff Agent   Retrieval Agent   Impact Agent   Writer Agent
        └────────────┴────────┬────────┴─────────────┘
                     Shared Task State (LangGraph)
                              │
                    Final Compliance Memo
                  (cited, JSON + human-readable)
```

- **Diff Agent** — aligns old vs. new circular text and extracts a structured delta (additions, removals, modifications) rather than passing raw circular text downstream
- **Retrieval Agent (RAG)** — embeds the internal policy document in ChromaDB and retrieves only the sections relevant to each change, compressing results into cited evidence summaries before handoff
- **Impact Agent** — reasons about business impact per change, flags potential compliance gaps, and assigns a confidence score that drives re-routing
- **Writer Agent** — synthesizes the distilled outputs into a final memo with citations and recommended actions
- **Orchestrator Agent** — parses intent, builds a dynamic task plan, owns the shared state, and re-routes to the Retrieval Agent on low-confidence impact assessments

## Tech Stack

| Layer | Choice |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | Gemini 1.5/2.0 Flash or Groq (Llama) |
| Embeddings | `bge-small-en` or Gemini embeddings |
| Vector DB | ChromaDB |
| Backend | FastAPI |
| Frontend | Streamlit |
| Eval / Charts | pandas + matplotlib |
| Tracing | LangSmith |
| Deployment | Docker + Render/Railway |

## Repository Structure

```
regtech-agent/
├── data/
│   ├── raw/                  # downloaded circular PDFs
│   ├── processed/            # parsed JSON docs
│   └── policy/               # mock internal policy doc
├── src/
│   ├── ingestion/             # PDF parsing, document store
│   ├── agents/                 # diff, retrieval, impact, writer, orchestrator
│   ├── graph/                  # LangGraph definition
│   ├── rag/                    # embeddings, vector store
│   ├── api/                    # FastAPI app
│   └── eval/                   # test set + evaluation harness
├── frontend/
│   └── app.py                 # Streamlit app
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Getting Started

```bash
# clone and enter the repo
git clone https://github.com/<your-username>/regtech-agent.git
cd regtech-agent

# install dependencies
pip install -r requirements.txt

# set environment variables
cp .env.example .env
# add your Gemini / Groq API keys to .env

# run ingestion on your circular pairs + policy doc
python src/ingestion/document_store.py

# start the API
uvicorn src.api.main:app --reload

# start the frontend (in a separate terminal)
streamlit run frontend/app.py
```

Or with Docker Compose:

```bash
docker compose -f docker/docker-compose.yml up --build
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/analyze` | POST | Submit a `doc_id` + query; triggers the Orchestrator and returns the memo |
| `/circulars` | GET | List ingested circulars |
| `/circulars/{id}/trace` | GET | Return the agent execution trace for a given analysis |
| `/eval/results` | GET | Return evaluation harness results |

## Evaluation

The system is validated against a manually labeled test set of 8–10 circular pairs, measuring:
- **Diff Agent** — precision/recall of detected changes vs. manually identified changes
- **Impact Agent** — agreement rate with manually assigned impact severity labels
- **End-to-end** — whether the final memo surfaces all high-impact changes

Results are available via `/eval/results` and summarized as a results table with charts.

## Disclaimer

This project uses a small set of manually curated circular pairs and a hand-written mock policy document for demonstration purposes. It is not a production compliance tool and should not be relied on for actual regulatory decisions.

## License

Add a license of your choice (e.g., MIT) before publishing.
