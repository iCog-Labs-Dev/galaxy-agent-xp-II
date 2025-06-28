from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agents.configs.config import Settings
from agents.utils.response_models import SuggestionRequest, SuggestionResponse, WorkflowSuggestionResponse, WorkflowSuggestionResponseItem
from agents.suggesting_agent import ToolSuggestionAgent
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent

app = FastAPI(title="Galaxy Tool Suggestion API")

# CORS setup
settings = Settings()
origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load agent once, passing settings from config
agent = ToolSuggestionAgent(
    embeddings_path=settings.embeddings_path,
    metadata_path=settings.metadata_path
)

# Load workflow suggestion agent
workflow_agent = WorkflowSuggestionAgent(
    embeddings_path=settings.workflow_embeddings_path,
    metadata_path=settings.workflow_metadata_path
)

@app.get("/")
def root():
    return {"message": "Welcome to the Galaxy Tool Suggestion API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/suggest", response_model=SuggestionResponse)
def suggest_tools(request: SuggestionRequest):
    results = agent.suggest_tools(request.query, request.top_k)
    return {"results": results}

@app.post("/suggest-workflows", response_model=WorkflowSuggestionResponse)
def suggest_workflows(request: SuggestionRequest):
    results = workflow_agent.suggest_workflows(request.query, request.top_k)
    return {"results": results}