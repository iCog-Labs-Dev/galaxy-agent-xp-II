from pydantic import BaseModel #type: ignore
from typing import Any

class WorkflowProperties(BaseModel):
    category: str
    workflow_repository: str
    has_readme: bool
    has_dockstore_yml: bool
    has_test_data: bool
    has_changelog: bool
    planemo_tests: str
    readme_content: str


class WorkflowFileProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    number_of_steps: int
    file_name: str
    raw_download_url: str
    tools_used_count: int
    
class ToolsInWorkflowFileProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    id: str
    name: str
    version: str
    owner: str
    tool_category: str
    tool_shed_url: str

class StepsInWorkflowFileProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    name: str
    type: str
    annotation: str
    tool_id: str | None
    tool_version: str | None
    inputs_count: int
    outputs_count: int

class StepInputsProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any


class StepOutputsProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    
class ToolProperties(BaseModel):
    id: str | None = None
    name: str
    description: str
    version: str
    help: str
    owner: str | None = None
    tool_category: str | None = None
    tool_shed_url: str | None = None


class ToolsInStepsProperties(BaseModel):
    id: str
    name: str
    version: str
    owner: str
    category: str
    tool_shed_url: str


class ToolMasterProperties(BaseModel):
    id: str | None = None
    name: str
    description: str
    version: str
    help: str


class ToolCategoryRow(BaseModel):
    id: str
    category: str


class ToolInputRow(BaseModel):
    id: str
    input_name: str
    input_type: str


class ToolOutputRow(BaseModel):
    id: str
    output_name: str
    output_format: str | None = None

class Tool(BaseModel):
    label: str = "tool"
    unique_key: Any = ["name", "version"]
    properties: ToolProperties

class InputProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    name: str
    type: str
    description: str
    optional: bool


class OutputProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    name: str
    type: str
    description: str
    optional: bool


class InputConnectionProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    input_name: str
    from_step_id: Any
    from_output_name: str


class StepSequenceRow(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    from_step_id: Any
    to_step_id: Any
    sequence_index: int
