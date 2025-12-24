import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

from agents.ingestion.Load.neo4j_client import Neo4jClient
from agents.graphRAG.pipeline.hybrid_rag_pipeline import HybridRAGPipeline

# ---------------- CONFIGURATION ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
os.environ.setdefault("GEMINI_API_KEY", "dummy_key")

# ---------------- FASTAPI SETUP ---------------- #
app = FastAPI(title="Galaxy HybridRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- REQUEST MODEL ---------------- #
class NLQueryRequest(BaseModel):
    query: str
    top_k: int = 5

# ---------------- PIPELINE INITIALIZATION ---------------- #
try:
    neo4j_client = Neo4jClient()
    hybrid_rag = HybridRAGPipeline(neo4j_client)
    logger.info("HybridRAG pipeline initialized successfully.")
except Exception as e:
    logger.warning(f"HybridRAG initialization failed: {e}")
    hybrid_rag = None

# ---------------- HEALTH CHECK ---------------- #
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ---------------- HYBRID RAG ENDPOINT ---------------- #
@app.post("/query-hybrid-rag")
def query_hybrid_rag(request: NLQueryRequest):
    """
    Intent-aware RAG endpoint:
    - Classifies query (tool/workflow/both)
    - Retrieves relevant context from Neo4j
    - Generates final answer via Gemini
    """
    if not hybrid_rag:
        raise HTTPException(status_code=500, detail="HybridRAG pipeline not initialized.")
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        result = hybrid_rag.run(request.query, top_k=request.top_k)
        return result
    except Exception as e:
        logger.exception("HybridRAG query failed")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- ENTRYPOINT ---------------- #
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Galaxy HybridRAG API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
