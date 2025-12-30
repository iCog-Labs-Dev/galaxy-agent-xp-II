# agents/app.py
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import yaml

from agents.utils.response_models import (
    SuggestionRequest, WorkflowSuggestionResponse, ToolSuggestionResponse
)
from tool_suggesting_agent import ToolSuggestionAgent
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent
from agents.summary_agent import summarize_tool_suggestions, summarize_workflow_suggestions
from agents.classification_service import classify_query
from generation.answer_generator import LLMAnswerGenerator
from agents.ingestion.Load.neo4j_client import Neo4jClient
from agents.summary_agent import SummaryAgent


# ---------------- CONFIGURATION ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def load_neo_config(path="agents/graphRAG/config/graph_db_config.yml"):
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
    neo_client = Neo4jClient("agents/graphRAG/config/graph_db_config.yml")

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
@app.post("/suggest-tools", response_model=ToolSuggestionResponse)
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
    uvicorn.run("agents.app:app", host="0.0.0.0", port=8000, reload=True)