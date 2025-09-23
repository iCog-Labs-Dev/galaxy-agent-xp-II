from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.utils.response_models import (
    SuggestionRequest,
    SuggestionResponse,
    WorkflowSuggestionResponse
)
from agents.suggesting_agent import ToolSuggestionAgent
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent
from agents.summary_agent import (
    summarize_tool_suggestions,
    summarize_workflow_suggestions
)
from agents.services.classification_service import classify_query   # ✅ NEW import

app = FastAPI(title="Galaxy Tool Suggestion API")

# ------------------ CORS SETUP ------------------ #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ AGENTS ---------------------- #
agent = ToolSuggestionAgent()
workflow_agent = WorkflowSuggestionAgent()

# ------------------ BASIC ENDPOINTS -------------- #
@app.get("/")
def root():
    return {"message": "Welcome to the Galaxy Tool Suggestion API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ------------------ TOOL ENDPOINTS -------------- #
@app.post("/suggest", response_model=SuggestionResponse)
def suggest_tools(request: SuggestionRequest):
    results = agent.suggest_tools(request.query, request.top_k)
    return {"results": results}

@app.post("/suggest-tools-enhanced")
def suggest_tools_enhanced(request: SuggestionRequest):
    result_from_e5 = agent.suggest_tools(request.query, request.top_k)
    results = summarize_tool_suggestions(result_from_e5, request.query)
    return {"results": results}

# ------------------ WORKFLOW ENDPOINTS ---------- #
@app.post("/suggest-workflows", response_model=WorkflowSuggestionResponse)
def suggest_workflows(request: SuggestionRequest):
    results = workflow_agent.suggest_workflows(request.query, request.top_k)
    return {"results": results}

@app.post("/suggest-workflows-enhanced")
def suggest_workflows_enhanced(request: SuggestionRequest):
    result_from_e5 = workflow_agent.suggest_workflows(request.query, request.top_k)
    results = summarize_workflow_suggestions(result_from_e5, request.query)
    return {"results": results}

# ------------------ GEMINI-POWERED ENDPOINT ----- #
@app.post("/recommend")
def recommend(request: SuggestionRequest):
    """
    Unified endpoint:
    - Gemini classifies query as 'tool', 'workflow', or 'both'
    - Routes to the correct agent(s)
    """
    category = classify_query(request.query)  #  Step 1: Gemini classification

    if category == "tool":
        tools = agent.suggest_tools(request.query, request.top_k)
        return {"type": "tool", "results": tools}

    elif category == "workflow":
        workflows = workflow_agent.suggest_workflows(request.query, request.top_k)
        return {"type": "workflow", "results": workflows}

    else:  # "both"
        tools = agent.suggest_tools(request.query, request.top_k)
        workflows = workflow_agent.suggest_workflows(request.query, request.top_k)
        return {
            "type": "both",
            "tool_results": tools,
            "workflow_results": workflows
        }
