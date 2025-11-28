# AUTO-GENERATED: NODE CLASSES
from pydantic import BaseModel
from typing import Any

class WorkflowProperties(BaseModel):
    name: str
    category: str
    readme: str

class Workflow(BaseModel):
    label: str = "workflow"
    description: str = "A workflow composed of tools and IO"
    properties: WorkflowProperties

class ToolProperties(BaseModel):
    name: str
    description: str
    version: str
    help: str

class Tool(BaseModel):
    label: str = "tool"
    properties: ToolProperties

class CategoryProperties(BaseModel):
    name: str

class Category(BaseModel):
    label: str = "category"
    properties: CategoryProperties

class InputProperties(BaseModel):
    description: str

class Input(BaseModel):
    label: str = "input"
    properties: InputProperties

class OutputProperties(BaseModel):
    description: str

class Output(BaseModel):
    label: str = "output"
    properties: OutputProperties

class KeywordProperties(BaseModel):
    name: str

class Keyword(BaseModel):
    label: str = "keyword"
    properties: KeywordProperties
