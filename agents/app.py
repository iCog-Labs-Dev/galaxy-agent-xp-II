# agents/app.py
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from agents.utils.response_models import (
    SuggestionRequest, SuggestionResponse, WorkflowSuggestionResponse
)
from agents.suggesting_agent import ToolSuggestionAgent
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent
from agents.summary_agent import summarize_tool_suggestions, summarize_workflow_suggestions
from agents.classification_service import classify_query

# ---------------- CONFIGURATION ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Ensure dummy-safe environment for CI/CD
os.environ.setdefault("GEMINI_API_KEY", "dummy_key")
os.environ.setdefault("OPENAI_API_KEY", "dummy_key")

# ---------------- FASTAPI SETUP ---------------- #
app = FastAPI(title="Galaxy Tool Suggestion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- AGENTS ---------------- #
try:
    agent = ToolSuggestionAgent()
    workflow_agent = WorkflowSuggestionAgent()
except Exception as e:
    logger.warning(f"Agent initialization skipped or failed in CI: {e}")
    agent = None
    workflow_agent = None

# ---------------- BASIC ROUTES ---------------- #
@app.get("/")
def root():
    return {"message": "Welcome to the Galaxy Tool Suggestion API!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---------------- TOOL ENDPOINTS ---------------- #
@app.post("/suggest", response_model=SuggestionResponse)
def suggest_tools(request: SuggestionRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Tool agent not initialized.")
    results = agent.suggest_tools(request.query, request.top_k)
    return {"results": results}


@app.post("/suggest-tools-enhanced")
def suggest_tools_enhanced(request: SuggestionRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Tool agent not initialized.")
    results = summarize_tool_suggestions(
        agent.suggest_tools(request.query, request.top_k),
        request.query
    )
    return {"results": results}


# ---------------- WORKFLOW ENDPOINTS ---------------- #
@app.post("/suggest-workflows", response_model=WorkflowSuggestionResponse)
def suggest_workflows(request: SuggestionRequest):
    if not workflow_agent:
        raise HTTPException(status_code=500, detail="Workflow agent not initialized.")
    results = workflow_agent.suggest_workflows(request.query, request.top_k)
    return {"results": results}


@app.post("/suggest-workflows-enhanced")
def suggest_workflows_enhanced(request: SuggestionRequest):
    if not workflow_agent:
        raise HTTPException(status_code=500, detail="Workflow agent not initialized.")
    results = summarize_workflow_suggestions(
        workflow_agent.suggest_workflows(request.query, request.top_k),
        request.query
    )
    return {"results": results}


# ---------------- UNIFIED RECOMMENDATION ---------------- #
@app.post("/recommend")
async def recommend(request: SuggestionRequest):
    try:
        category = classify_query(request.query)

        if category == "tool":
            tools = agent.suggest_tools(request.query, request.top_k)
            return {"type": "tool", "results": tools}

        elif category == "workflow":
            workflows = workflow_agent.suggest_workflows(request.query, request.top_k)
            return {"type": "workflow", "results": workflows}

        else:
            tools = agent.suggest_tools(request.query, request.top_k)
            workflows = workflow_agent.suggest_workflows(request.query, request.top_k)
            return {
                "type": "both",
                "tool_results": tools,
                "workflow_results": workflows
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- ENTRYPOINT (for local run only) ---------------- #
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting FastAPI app on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
