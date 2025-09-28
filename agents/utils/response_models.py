from pydantic import BaseModel
from typing import List, Optional

# ------------------ REQUEST MODEL ------------------ #
class SuggestionRequest(BaseModel):
    query: str
    top_k: int = 5

# ------------------ TOOL MODELS ------------------ #
class ToolSuggestion(BaseModel):
    id: str                      # Include ID
    name: str
    description: str
    help: Optional[str] = ""
    category: str
    version: str
    score: float

class SuggestionResponse(BaseModel):
    results: List[ToolSuggestion]

# ------------------ WORKFLOW MODELS ------------------ #
class WorkflowSuggestionResponseItem(BaseModel):
    name: str
    category: str
    tools_used: List[str]                  
    download_url: Optional[str] = None     
    readme_excerpt: str
    score: float

class WorkflowSuggestionResponse(BaseModel):
    results: List[WorkflowSuggestionResponseItem]
