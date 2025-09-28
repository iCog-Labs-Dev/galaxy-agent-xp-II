from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agents.routes.recommend_route import router as recommend_router
from agents.utils.response_models import (
    SuggestionRequest, SuggestionResponse, WorkflowSuggestionResponse
)
from agents.suggesting_agent import ToolSuggestionAgent
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent
from agents.summary_agent import summarize_tool_suggestions, summarize_workflow_suggestions

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
    results = summarize_tool_suggestions(
        agent.suggest_tools(request.query, request.top_k),
        request.query
    )
    return {"results": results}

# ------------------ WORKFLOW ENDPOINTS ---------- #
@app.post("/suggest-workflows", response_model=WorkflowSuggestionResponse)
def suggest_workflows(request: SuggestionRequest):
    results = workflow_agent.suggest_workflows(request.query, request.top_k)
    return {"results": results}

@app.post("/suggest-workflows-enhanced")
def suggest_workflows_enhanced(request: SuggestionRequest):
    results = summarize_workflow_suggestions(
        workflow_agent.suggest_workflows(request.query, request.top_k),
        request.query
    )
    return {"results": results}

# ------------------ GEMINI-POWERED ENDPOINT ----- #
app.include_router(recommend_router)
