# AUTO-GENERATED: NODE CLASSES
from pydantic import BaseModel
from typing import Any

class WorkflowProperties(BaseModel):
    name: str
    category: str
    readme: str
    workflow_repository: str
    file_name: str
    raw_download_url: str
    number_of_steps: int
    has_readme: bool
    has_changelog: bool
    has_test_data: bool

class Workflow(BaseModel):
    label: str = "workflow"
    unique_key: Any = ['workflow_repository']
    description: str = "A workflow composed of tools and IO"
    properties: WorkflowProperties

class ToolProperties(BaseModel):
    name: str
    description: str
    version: str
    help: str

class Tool(BaseModel):
    label: str = "tool"
    unique_key: Any = []
    properties: ToolProperties

class CategoryProperties(BaseModel):
    name: str

class Category(BaseModel):
    label: str = "category"
    unique_key: Any = ['name']
    properties: CategoryProperties

class InputProperties(BaseModel):
    description: str

class Input(BaseModel):
    label: str = "input"
    unique_key: Any = []
    properties: InputProperties

class OutputProperties(BaseModel):
    description: str

class Output(BaseModel):
    label: str = "output"
    unique_key: Any = []
    properties: OutputProperties

class KeywordProperties(BaseModel):
    name: str

class Keyword(BaseModel):
    label: str = "keyword"
    unique_key: Any = []
    properties: KeywordProperties
