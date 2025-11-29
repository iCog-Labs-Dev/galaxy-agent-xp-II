# AUTO-GENERATED: RELATIONSHIP CLASSES
from pydantic import BaseModel
from typing import Any

from .schema_nodes import *

from typing import Optional

class WorkflowTool(BaseModel):
    label: str = "USES_TOOL"
    source: Workflow
    target: Tool
    properties: Optional[BaseModel] = None

class WorkflowCategory(BaseModel):
    label: str = "BELONGS_TO"
    source: Workflow
    target: Category
    properties: Optional[BaseModel] = None

class ToolCategory(BaseModel):
    label: str = "BELONGS_TO"
    source: Tool
    target: Category
    properties: Optional[BaseModel] = None

class WorkflowInput(BaseModel):
    label: str = "HAS_INPUT"
    source: Workflow
    target: Input
    properties: Optional[BaseModel] = None

class WorkflowOutput(BaseModel):
    label: str = "HAS_OUTPUT"
    source: Workflow
    target: Output
    properties: Optional[BaseModel] = None

class WorkflowKeyword(BaseModel):
    label: str = "HAS_KEYWORD"
    source: Workflow
    target: Keyword
    properties: Optional[BaseModel] = None

class ToolKeyword(BaseModel):
    label: str = "HAS_KEYWORD"
    source: Tool
    target: Keyword
    properties: Optional[BaseModel] = None

class ToolSimilarProperties(BaseModel):
    score: float

class ToolSimilar(BaseModel):
    label: str = "SIMILAR_TO"
    source: Tool
    target: Tool
    properties: ToolSimilarProperties
