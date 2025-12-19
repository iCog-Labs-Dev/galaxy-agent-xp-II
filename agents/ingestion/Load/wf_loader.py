import json
from tqdm import tqdm
from extract.parser import WorkflowParser
from extract.normalize import Normalizer
from transform.wf_node_builder import NodeBuilder
from transform.wf_rel_builder import RelationshipBuilder
from Load.neo4j_client import Neo4jClient

class GraphLoader:
    def __init__(self, neo4j: Neo4jClient):
        self.neo = neo4j
        self.parser = WorkflowParser()
        self.norm = Normalizer()
        self.nodes = NodeBuilder()
        self.rels = RelationshipBuilder()

    def import_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            workflows = json.load(f)
        print(f"🔍 Processing {len(workflows)} workflows...")
        for wf in tqdm(workflows, desc="Workflows", unit="wf"):
            self._process_workflow(wf)

    def _process_workflow(self, wf):
        category_name = self.norm.normalize_category(wf["category"])
        category_node = self.nodes.create_category(category_name)
        self.neo.merge_node(category_node["label"], category_node["properties"], unique_key="category_id")

        for wf_file in wf.get("workflow_files", []):
            self._process_workflow_file(wf_file, wf, category_node)

    def _process_workflow_file(self, wf_file, wf_root, category_node):
        workflow_name = wf_file["workflow_name"].strip()
        workflow_node = self.nodes.create_workflow({
            "workflow_repository": workflow_name,
            "category": category_node["properties"]["name"],
            "file_name": wf_file.get("file_name"),
            "raw_download_url": wf_file.get("raw_download_url"),
            "number_of_steps": wf_file.get("number_of_steps"),
            "readme": wf_root.get("readme_content", ""),
            "has_readme": wf_root.get("has_readme", False),
            "has_changelog": wf_root.get("has_changelog", False),
            "has_test_data": wf_root.get("has_test_data", False),
            "planemo_tests": wf_root.get("planemo_tests", []),
            "embedding": wf_root.get("embedding")  # <-- Add embedding here if available
        })
        workflow_id = workflow_node["properties"]["workflow_id"]
        self.neo.merge_node(workflow_node["label"], workflow_node["properties"], unique_key="workflow_id")

        # Category → Workflow
        rel = self.rels.workflow_category(workflow_node, category_node)
        self.neo.merge_rel(*rel)

        # Steps
        for step in wf_file.get("steps", []):
            self._process_step(step, workflow_id, workflow_node)

        # Workflow-level inputs/outputs
        inputs, outputs = self.parser.extract_io(wf_root.get("readme_content", ""))
        for inp in inputs:
            input_node = self.nodes.create_input_node(workflow_id, None, inp, inp)
            self.neo.merge_node(input_node["label"], input_node["properties"], unique_key="input_uid")
            self.neo.merge_rel(*self.rels.workflow_input(workflow_node, input_node))

        for out in outputs:
            output_node = self.nodes.create_output_node(workflow_id, None, out, out)
            self.neo.merge_node(output_node["label"], output_node["properties"], unique_key="output_uid")
            self.neo.merge_rel(*self.rels.workflow_output(workflow_node, output_node))

    def _process_step(self, step, workflow_id, workflow_node):
        step_node = self.nodes.create_step(step, workflow_id)
        self.neo.merge_node("Step", step_node["properties"], unique_key="step_uid")
        self.neo.merge_rel(*self.rels.workflow_step(workflow_node, step_node))

        # Step → Tool (USES_TOOL)
        tool_id = step.get("tool_id")
        if tool_id:
            tool_node = self.nodes.create_tool(
                tool_id,
                step.get("tool_version", ""),
                step.get("tool_repo", ""),
                step.get("tool_owner", "")
            )
            # Add embedding if available in the step/tool
            if "embedding" in step:
                tool_node["properties"]["embedding"] = step["embedding"]

            self.neo.merge_node(tool_node["label"], tool_node["properties"], unique_key="tool_id")
            self.neo.merge_rel(*self.rels.step_tool(step_node, tool_node))

        # Step Inputs
        for inp in step.get("inputs", []):
            input_node = self.nodes.create_input_node(workflow_id, step.get("step_id"), inp.get("name", ""), inp.get("description", ""))
            self.neo.merge_node(input_node["label"], input_node["properties"], unique_key="input_uid")
            self.neo.merge_rel(*self.rels.step_input(step_node, input_node))

        # Step Outputs
        for out in step.get("outputs", []):
            output_node = self.nodes.create_output_node(workflow_id, step.get("step_id"), out.get("name", ""), out.get("description", ""))
            self.neo.merge_node(output_node["label"], output_node["properties"], unique_key="output_uid")
            self.neo.merge_rel(*self.rels.step_output(step_node, output_node))
