import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from pathlib import Path

from agents.graphRAG.retrieval.gemini_llm import GeminiLLM
from agents.graphRAG.pipeline.rag_pipeline import GraphRAGPipeline
from agents.ingestion.Load.neo4j_client import Neo4jClient

# ---------------- CONFIGURATION ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
os.environ.setdefault("GEMINI_API_KEY", "dummy_key")
os.environ.setdefault("OPENAI_API_KEY", "dummy_key")

# ---------------- FASTAPI SETUP ---------------- #
app = FastAPI(title="Galaxy GraphRAG API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- LOAD SCHEMA ---------------- #
schema_file = Path(__file__).parent / "retrieval/neo4j_schema.json"
try:
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_json = json.load(f)
    schema_nodes = schema_json.get("nodes", {})
    schema_rels = schema_json.get("relationships", {})
    logger.info(f"Loaded Neo4j schema with {len(schema_nodes)} nodes and {len(schema_rels)} relationships.")
except Exception as e:
    logger.error(f"Failed to load Neo4j schema: {e}")
    schema_nodes, schema_rels = {}, {}

# ---------------- GRAPH RAG INITIALIZATION ---------------- #
try:
    neo4j_client = Neo4jClient()
    llm = GeminiLLM()
    rag = GraphRAGPipeline(neo4j_client.driver, llm, schema_nodes, schema_rels)
    logger.info(f"Pipeline initialized: {rag}")
except Exception as e:
    logger.warning(f"GraphRAG initialization failed: {e}")
    rag = None

# ---------------- REQUEST MODELS ---------------- #
class NLQueryRequest(BaseModel):
    query: str


@app.post("/query-graphrag")
def query_graphrag(request: NLQueryRequest):
    """
    Accepts natural language query, converts to Cypher, executes, 
    and returns ONLY the Cypher and concise human-readable answer.
    """
    if not rag:
        raise HTTPException(status_code=500, detail="GraphRAG pipeline not initialized.")
    try:
        result = rag.run(request.query)
        return {
            "cypher": result.get("cypher"),
            "answer": result.get("answer")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GraphRAG query failed: {e}")


# ---------------- ENTRYPOINT ---------------- #
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting FastAPI app on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
