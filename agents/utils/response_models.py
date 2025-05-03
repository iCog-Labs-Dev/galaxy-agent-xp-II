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
