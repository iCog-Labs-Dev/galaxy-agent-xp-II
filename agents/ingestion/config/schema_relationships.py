# AUTO-GENERATED: RELATIONSHIP CLASSES
from pydantic import BaseModel
from typing import Any

from .schema_nodes import *

class WorkflowTool(BaseModel):
    source: Workflow
    target: Tool

class WorkflowCategory(BaseModel):
    source: Workflow
    target: Category

class ToolCategory(BaseModel):
    source: Tool
    target: Category

class WorkflowInput(BaseModel):
    source: Workflow
    target: Input

class WorkflowOutput(BaseModel):
    source: Workflow
    target: Output

class WorkflowKeyword(BaseModel):
    source: Workflow
    target: Keyword

class ToolKeyword(BaseModel):
    source: Tool
    target: Keyword

class ToolSimilarProperties(BaseModel):
    score: float

class ToolSimilar(BaseModel):
    source: Tool
    target: Tool
    properties: ToolSimilarProperties
