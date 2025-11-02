from pydantic import BaseModel
from typing import List, Optional

# ------------------ REQUEST MODEL ------------------ #
class SuggestionRequest(BaseModel):
    query: str
    top_k: int = 5

# ------------------ TOOL MODELS ------------------ #
class ToolSuggestion(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    help: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    score: Optional[float] = None

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
