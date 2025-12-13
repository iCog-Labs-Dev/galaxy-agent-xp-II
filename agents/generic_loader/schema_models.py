from typing import List
from pydantic import BaseModel


class NodeSpec(BaseModel):
    name: str
    label: str
    file: str
    id_fields: List[str]
    id_property: str
    prop_fields: List[str] = []


class RelationshipSpec(BaseModel):
    type: str
    file: str
    from_: str
    to: str
    from_id_fields: List[str]
    to_id_fields: List[str]
    prop_fields: List[str] = []
    set_source_target: bool = False


class LoaderConfig(BaseModel):
    nodes: List[NodeSpec]
    relationships: List[RelationshipSpec]


# Default config instances for current workflow/tool CSVs
DEFAULT_CONFIG = LoaderConfig(
    nodes=[
        NodeSpec(
            name="Category",
            label="Category",
            file="workflow_files.csv",
            id_fields=["category"],
            id_property="category_id",
            prop_fields=["category"],
        ),
        NodeSpec(
            name="Workflow",
            label="Workflow",
            file="workflow_files.csv",
            id_fields=["workflow_repository", "file_name"],
            id_property="workflow_id",
            prop_fields=["workflow_repository", "category", "file_name", "raw_download_url", "number_of_steps"],
        ),
        NodeSpec(
            name="Step",
            label="Step",
            file="workflow_steps.csv",
            id_fields=["workflow_repository", "file_name", "step_id"],
            id_property="step_uid",
            prop_fields=["workflow_repository", "file_name", "step_id", "name", "type", "annotation", "tool_id", "tool_version"],
        ),
        NodeSpec(
            name="Input",
            label="Input",
            file="step_inputs.csv",
            id_fields=["workflow_repository", "file_name", "step_id", "name"],
            id_property="input_uid",
            prop_fields=["workflow_repository", "file_name", "step_id", "name", "description"],
        ),
        NodeSpec(
            name="Output",
            label="Output",
            file="step_outputs.csv",
            id_fields=["workflow_repository", "file_name", "step_id", "name"],
            id_property="output_uid",
            prop_fields=["workflow_repository", "file_name", "step_id", "name", "description"],
        ),
        NodeSpec(
            name="Tool",
            label="Tool",
            file="tools_used.csv",
            id_fields=["id"],
            id_property="tool_id",
            prop_fields=["id", "name", "version", "owner", "tool_category", "tool_shed_url"],
        ),
    ],
    relationships=[
        RelationshipSpec(
            type="HAS_WORKFLOW",
            file="workflow_files.csv",
            from_="Category",
            to="Workflow",
            from_id_fields=["category"],
            to_id_fields=["workflow_repository", "file_name"],
        ),
        RelationshipSpec(
            type="HAS_STEP",
            file="workflow_steps.csv",
            from_="Workflow",
            to="Step",
            from_id_fields=["workflow_repository", "file_name"],
            to_id_fields=["workflow_repository", "file_name", "step_id"],
            prop_fields=["step_id"],
        ),
        RelationshipSpec(
            type="STEP_REQUIRES",
            file="step_inputs.csv",
            from_="Step",
            to="Input",
            from_id_fields=["workflow_repository", "file_name", "step_id"],
            to_id_fields=["workflow_repository", "file_name", "step_id", "name"],
        ),
        RelationshipSpec(
            type="STEP_GENERATES",
            file="step_outputs.csv",
            from_="Step",
            to="Output",
            from_id_fields=["workflow_repository", "file_name", "step_id"],
            to_id_fields=["workflow_repository", "file_name", "step_id", "name"],
        ),
        RelationshipSpec(
            type="FEEDS_INTO",
            file="step_input_connections.csv",
            from_="Output",
            to="Input",
            from_id_fields=["workflow_repository", "file_name", "from_step_id", "from_output_name"],
            to_id_fields=["workflow_repository", "file_name", "step_id", "input_name"],
            prop_fields=["input_name"],
            set_source_target=True,
        ),
        RelationshipSpec(
            type="WORKFLOW_USES_TOOL",
            file="tools_used.csv",
            from_="Workflow",
            to="Tool",
            from_id_fields=["workflow_repository", "file_name"],
            to_id_fields=["id"],
        ),
    ],
)
