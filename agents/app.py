from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from configs.config import Settings
from utils.response_models import SuggestionRequest, SuggestionResponse
from suggesting_agent import ToolSuggestionAgent

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

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/suggest", response_model=SuggestionResponse)
def suggest_tools(request: SuggestionRequest):
    results = agent.suggest_tools(request.query, request.top_k)
    return {"results": results}
