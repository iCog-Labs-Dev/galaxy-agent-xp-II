from pydantic import BaseModel
from typing import List

class SuggestionRequest(BaseModel):
    query: str
    top_k: int = 5

class ToolSuggestion(BaseModel):
    name: str
    description: str
    help: str
    category: str
    score: float

class SuggestionResponse(BaseModel):
    results: List[ToolSuggestion]


class WorkflowSuggestionResponseItem(BaseModel):
    name: str
    category: str
    tools_used: List[str]
    has_readme: bool
    readme_excerpt: str
    score: float

class WorkflowSuggestionResponse(BaseModel):
    results: List[WorkflowSuggestionResponseItem]
