# Load/wf_loader.py
import json
from tqdm import tqdm
from extract.parser import WorkflowParser
from extract.normalize import Normalizer
from transform.wf_node_builder import NodeBuilder
from transform.wf_rel_builder import RelationshipBuilder
from Load.neo4j_client import Neo4jClient


class GraphLoader:

    def __init__(self, neo: Neo4jClient):
        self.neo = neo
        self.parser = WorkflowParser()
        self.norm = Normalizer()
        self.nodes = NodeBuilder()
        self.rels = RelationshipBuilder()

    def import_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            workflows = json.load(f)

        print(f"🔍 Processing {len(workflows)} workflows...")
        for wf in tqdm(workflows, unit="wf"):
            self._process_workflow(wf)

    def _process_workflow(self, wf):

        # -----------------------
        # Category
        # -----------------------
        category_name = self.norm.normalize_category(wf.get("category", "Unknown"))
        category = self.nodes.create_category(category_name)
        self.neo.merge_node("Category", category["properties"], unique_key="category_id")

        # -----------------------
        # Root Workflow (ONLY embedding lives here)
        # -----------------------
        root = self.nodes.create_workflow(
            name=wf["workflow_repository"],
            category=category_name,
            root=True,
            readme=wf.get("readme_content", ""),
            has_readme=wf.get("has_readme", False),
            has_changelog=wf.get("has_changelog", False),
            has_test_data=wf.get("has_test_data", False),
            planemo_tests=wf.get("planemo_tests", []),
            embedding=wf.get("embedding")
        )

        self.neo.merge_node("Workflow", root["properties"], unique_key="workflow_id")
        self.neo.merge_rel(*self.rels.workflow_category(root, category))

        # -----------------------
        # File Workflows (NO embedding)
        # -----------------------
        for wf_file in wf.get("workflow_files", []):
            self._process_workflow_file(wf, wf_file, root, category)

    def _process_workflow_file(self, wf_root, wf_file, root_node, category):

        file_node = self.nodes.create_workflow(
            name=wf_file["workflow_name"],
            category=category["properties"]["name"],
            root=False,
            file_name=wf_file["file_name"],
            download_url=wf_file.get("raw_download_url"),
            number_of_steps=wf_file.get("number_of_steps"),
            readme=wf_root.get("readme_content", "")
        )

        self.neo.merge_node("Workflow", file_node["properties"], unique_key="workflow_id")

        self.neo.merge_rel(*self.rels.workflow_category(file_node, category))
        self.neo.merge_rel(
            "HAS_IMPLEMENTATION",
            "Workflow", {"workflow_id": root_node["properties"]["workflow_id"]},
            "Workflow", {"workflow_id": file_node["properties"]["workflow_id"]}
        )

        workflow_id = file_node["properties"]["workflow_id"]

        # -----------------------
        # Steps
        # -----------------------
        for step in wf_file.get("steps", []):
            step_node = self.nodes.create_step(step, workflow_id)
            self.neo.merge_node("Step", step_node["properties"], unique_key="step_uid")
            self.neo.merge_rel(*self.rels.workflow_step(file_node, step_node))

            for inp in step.get("inputs", []):
                i = self.nodes.create_input(
                    workflow_id,
                    step_node["properties"]["step_uid"],
                    inp["name"],
                    inp["description"]
                )
                self.neo.merge_node("Input", i["properties"], unique_key="input_uid")
                self.neo.merge_rel(*self.rels.step_input(step_node, i))

            for out in step.get("outputs", []):
                o = self.nodes.create_output(
                    workflow_id,
                    step_node["properties"]["step_uid"],
                    out["name"],
                    out["description"]
                )
                self.neo.merge_node("Output", o["properties"], unique_key="output_uid")
                self.neo.merge_rel(*self.rels.step_output(step_node, o))
