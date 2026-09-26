"""
Central configuration for the RegTech Multi-Agent System.
Loads environment variables and exposes shared constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM provider ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "groq"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

# --- Embeddings ---
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # self-hosted, free

# --- Vector store ---
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_store")
COLLECTION_NAME = "internal_policy_docs"

# --- Chunking ---
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# --- Retrieval ---
TOP_K_RETRIEVAL = 4

# --- Orchestrator / context engineering ---
IMPACT_CONFIDENCE_THRESHOLD = float(os.getenv("IMPACT_CONFIDENCE_THRESHOLD", 0.6))
MAX_RETRIES = 2

# --- Paths ---
DATA_RAW_DIR = "./data/raw"
DATA_PROCESSED_DIR = "./data/processed"
DATA_POLICY_DIR = "./data/policy"
