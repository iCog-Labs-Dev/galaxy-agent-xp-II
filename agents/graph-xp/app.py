# agents/app.py
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from pydantic import BaseModel

# Ensure project paths are available when running as a module
APP_DIR = Path(__file__).resolve().parent
AGENTS_ROOT = APP_DIR.parent
PROJECT_ROOT = AGENTS_ROOT.parent
GENERATION_DIR = APP_DIR / "generation"
# Insert paths in reverse priority order so sys.path ends up preferring generation > app dir > agents root > project root
for path in (PROJECT_ROOT, AGENTS_ROOT, APP_DIR, GENERATION_DIR):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)

from utils.response_models import (
    SuggestionRequest,
    SuggestionResponse,
    WorkflowSuggestionResponse,
)
from classification_service import classify_query
from generation.answer_generator import LLMAnswerGenerator
from summary_agent import SummaryAgent, summarize_tool_suggestions, summarize_workflow_suggestions
from tool_suggesting_agent import ToolSuggestionAgent
from workflow_suggestion_agent import WorkflowSuggestionAgent


# ---------------- CONFIGURATION ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def load_neo_config(path="agents/graph-xp/config/graph_db_config.yml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("neo4j", {})
    except FileNotFoundError:
        logger.error(f"Neo4j config file not found: {path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading Neo4j config: {e}")
        return {}

neo_cfg = load_neo_config()


class Neo4jClient:
    """Lightweight Neo4j client wrapper (no ingestion dependency)."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def run_query(self, cypher: str, parameters: Optional[dict] = None):
        with self.driver.session() as session:
            result = session.run(cypher, **(parameters or {}))
            return [dict(rec) for rec in result]

    def close(self):
        self.driver.close()

# ---------------- FASTAPI SETUP ---------------- #
app = FastAPI(title="Galaxy Tool & Workflow Suggestion API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- AGENTS ---------------- #
try:
    neo_uri = neo_cfg.get("uri") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo_user = neo_cfg.get("user") or os.getenv("NEO4J_USER", "neo4j")
    neo_password = neo_cfg.get("password") or os.getenv("NEO4J_PASSWORD", "neo4j")

    neo_client = Neo4jClient(neo_uri, neo_user, neo_password)

    tool_agent = ToolSuggestionAgent(neo_client)
    workflow_agent = WorkflowSuggestionAgent(neo_client)
    summary_agent = SummaryAgent()

    answer_gen = LLMAnswerGenerator()

except Exception as e:
    logger.error(f"Agent initialization failed: {e}")
    tool_agent = workflow_agent = summary_agent = answer_gen = None

# ---------------- REQUEST MODELS ---------------- #
class NLQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

# ---------------- BASIC ROUTES ---------------- #
@app.get("/")
def root():
    return {"message": "Welcome to the Galaxy Tool & Workflow Suggestion API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ---------------- Tool Agent ---------------- #
@app.post("/suggest-tools", response_model=SuggestionResponse)
def suggest_tools(request: SuggestionRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    results = tool_agent.suggest_tools(request.query, request.top_k)
    return {"results": results}

@app.post("/suggest-tools-enhanced")
def suggest_tools_enhanced(request: SuggestionRequest):
    tools = tool_agent.suggest_tools(request.query, request.top_k)
    summary = summary_agent.summarize_tools_suggestions(tools, request.query)

    return {
        "results": tools,
        "summary": summary
    }

# ---------------- WORKFLOW ENDPOINT ---------------- #
@app.post("/suggest-workflows", response_model=WorkflowSuggestionResponse)
def suggest_workflows(request: SuggestionRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    results = workflow_agent.suggest_workflows(request.query, request.top_k)
    return {"results": results}


@app.post("/suggest-workflows-enhanced")
def suggest_workflows_enhanced(request: SuggestionRequest):
    workflows = workflow_agent.suggest_workflows(request.query, request.top_k)
    summary = summary_agent.summarize_workflows_suggestions(workflows, request.query)

    return {
        "results": workflows,
        "summary": summary
    }


# ---------------- UNIFIED RECOMMENDATION ---------------- #
@app.post("/recommend")
def recommend(request: SuggestionRequest):
    if not tool_agent or not workflow_agent or not answer_gen:
        raise HTTPException(status_code=500, detail="Agents not fully initialized.")

    try:
        # Get the predicted intent
        category_data = classify_query(request.query)
        category_label = category_data.get("label", "")

        tools = []
        workflows = []

        # Fetch only what's relevant
        if category_label in ("tool", "both"):
            tools = tool_agent.suggest_tools(request.query, request.top_k)

        if category_label in ("workflow", "both"):
            workflows = workflow_agent.suggest_workflows(request.query, request.top_k)

        # Generate the answer
        result = answer_gen.generate(
            intent=category_label,
            query=request.query,
            tools=tools,
            workflows=workflows
        )

        response = {}

        # Include only the relevant outputs
        if category_label == "tool":
            response["tools"] = [t.get("name") for t in tools]
        elif category_label == "workflow":
            response["workflows"] = [w.get("name") for w in workflows]
        elif category_label == "both":
            response["tools"] = [t.get("name") for t in tools]
            response["workflows"] = [w.get("name") for w in workflows]

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- ENTRYPOINT ---------------- #
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting FastAPI app on http://localhost:8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)