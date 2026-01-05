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

class Workflow(BaseModel):
    label: str = "workflow"
    unique_key: Any = ["workflow_repository"]
    description: str = "A workflow composed of tools and IO"
    properties: WorkflowProperties


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
    
class InputConncectionProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    input_name: str
    from_step_id: Any
    from_output_name: str


class WorkflowFile(BaseModel):
    label: str = "workflow_file"
    unique_key: Any = ["workflow_repository", "file_name"]
    properties: WorkflowFileProperties

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

class Tool(BaseModel):
    label: str = "tool"
    unique_key: Any = ["name", "version"]
    properties: ToolProperties


class ToolUsedProperties(BaseModel):
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


class ToolUsed(BaseModel):
    label: str = "tool_used"
    unique_key: Any = ["workflow_repository", "file_name", "id", "version"]
    properties: ToolUsedProperties

class CategoryProperties(BaseModel):
    name: str

class Category(BaseModel):
    label: str = "category"
    unique_key: Any = ["name"]
    properties: CategoryProperties

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

class Input(BaseModel):
    label: str = "input"
    unique_key: Any = ["workflow_repository", "file_name", "step_id", "name"]
    properties: InputProperties

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

class Output(BaseModel):
    label: str = "output"
    unique_key: Any = ["workflow_repository", "file_name", "step_id", "name"]
    properties: OutputProperties

class KeywordProperties(BaseModel):
    name: str

class Keyword(BaseModel):
    label: str = "keyword"
    unique_key: Any = ["name"]
    properties: KeywordProperties

class StepProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    name: str
    type: str
    annotation: str
    tool_id: str
    tool_version: str
    inputs_count: int
    outputs_count: int


class Step(BaseModel):
    label: str = "step"
    unique_key: Any = ["workflow_repository", "file_name", "step_id"]
    description: str = "A single step in a workflow"
    properties: StepProperties


class InputConnectionProperties(BaseModel):
    category: str
    workflow_repository: str
    workflow_name: str
    file_name: str
    step_id: Any
    input_name: str
    from_step_id: Any
    from_output_name: str


class InputConnection(BaseModel):
    label: str = "input_connection"
    unique_key: Any = ["workflow_repository", "file_name", "step_id", "input_name", "from_step_id", "from_output_name"]
    properties: InputConnectionProperties
