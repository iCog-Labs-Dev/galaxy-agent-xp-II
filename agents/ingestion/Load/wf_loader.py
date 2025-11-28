import json
from tqdm import tqdm
from extract.parser import WorkflowParser
from extract.normalize import Normalizer
# from transform.wf_node_builder import NodeBuilder
from transform.node_builder import GenericNodeBuilder
from transform.wf_rel_builder import RelationshipBuilder
from Load.neo4j_client import Neo4jClient
from config.schema_nodes import Category, CategoryProperties,Workflow ,WorkflowProperties

class GraphLoader:
    def __init__(self, neo4j: Neo4jClient):
        self.neo = neo4j
        self.parser = WorkflowParser()
        self.norm = Normalizer()
        # self.nodes = NodeBuilder()
        self.nodes = GenericNodeBuilder()
        self.rels = RelationshipBuilder()

    def import_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            workflows = json.load(f)
        print(f"🔍 Processing {len(workflows)} workflows... - wf_loader.py:23")
        for wf in tqdm(workflows, desc="Workflows", unit="wf"):
            self._process_workflow(wf)

    def _process_workflow(self, wf):
        # Category node
        # category_name = self.norm.normalize_category(wf["category"])
        # node = self.nodes.build_node(category_name)
        category = Category(properties=CategoryProperties(name="Tools"))
        print(category, "category - wf_loader.py:32")
        cat_node = self.nodes.build_node(category)
        print(cat_node, "node - wf_loader.py:34")
        self.neo.merge_node_2(cat_node)

        # category = Category(properties=CategoryProperties(name=wf["category"]))
        # self.neo.merge_node_2(category)

        # Iterate workflow files
        for wf_file in wf.get("workflow_files", []):
            self._process_workflow_file(wf_file, wf, cat_node)

    def _process_workflow_file(self, wf_file, wf_root, cat_node):
        print(wf_file, "node - wf_loader.py:45")
        
        workflow_props = WorkflowProperties(
            name=wf_file["workflow_name"].strip(),
            category=cat_node["properties"]["name"],
            readme=wf_root.get("readme_content", ""),
            file_name=wf_file.get("file_name"),
            raw_download_url=wf_file.get("raw_download_url"),
            number_of_steps=wf_file.get("number_of_steps"),
            has_readme=wf_root.get("has_readme", False),
            has_changelog=wf_root.get("has_changelog", False),
            has_test_data=wf_root.get("has_test_data", False),
        )
        
        workflow_model = Workflow(properties=workflow_props)
        workflow_node = self.nodes.build_node(workflow_model)

        # workflow_name = wf_file["workflow_name"].strip()
        # workflow_node = self.nodes.build_node({
        #     "workflow_repository": workflow_name,
        #     "category": cat_node["properties"]["name"],
        #     "file_name": wf_file.get("file_name"),
        #     "raw_download_url": wf_file.get("raw_download_url"),
        #     "number_of_steps": wf_file.get("number_of_steps"),
        #     "readme": wf_root.get("readme_content", ""),
        #     "has_readme": wf_root.get("has_readme", False),
        #     "has_changelog": wf_root.get("has_changelog", False),
        #     "has_test_data": wf_root.get("has_test_data", False),
        #     "planemo_tests": wf_root.get("planemo_tests", [])
        # })
        workflow_id = workflow_node["properties"]["id"]
        self.neo.merge_node_2(workflow_node)

        # # Category → Workflow
        # rel = self.rels.workflow_category(workflow_node, cat_node)
        # self.neo.merge_rel(*rel)

        # # Steps
        # for step in wf_file.get("steps", []):
        #     self._process_step(step, workflow_id, workflow_node)

        # # Workflow-level inputs/outputs from README
        # inputs, outputs = self.parser.extract_io(wf_root.get("readme_content", ""))
        # for inp in inputs:
        #     input_node = self.nodes.build_node(workflow_id, None, inp, inp)
        #     self.neo.merge_node(input_node["label"], input_node["properties"], unique_key="input_uid")
        #     self.neo.merge_rel(*self.rels.workflow_input(workflow_node, input_node))

        # for out in outputs:
        #     output_node = self.nodes.build_node(workflow_id, None, out, out)
        #     self.neo.merge_node(output_node["label"], output_node["properties"], unique_key="output_uid")
        #     self.neo.merge_rel(*self.rels.workflow_output(workflow_node, output_node))

    def _process_step(self, step, workflow_id, workflow_node):
        step_node = self.nodes.build_node(step, workflow_id)
        try:
            self.neo.merge_node("Step", step_node["properties"], unique_key="step_uid")
        except Exception as e:
            print(f"[wf_loader][error] failed to merge Step node: {e} - wf_loader.py:103")
            return

        # Workflow → Step
        rel = self.rels.workflow_step(workflow_node, step_node)
        # print("[wf_loader] creating rel workflow->step with:", rel)
        try:
            self.neo.merge_rel(*rel)
        except Exception as e:
            print(f"[wf_loader][error] failed to merge workflow>step rel: {e} - wf_loader.py:112")
            return

        # Step Inputs
        for inp in step.get("inputs", []):
            input_node = self.nodes.build_node(workflow_id, step.get("step_id"), inp.get("name", ""), inp.get("description", ""))
            self.neo.merge_node(input_node["label"], input_node["properties"], unique_key="input_uid")
            self.neo.merge_rel(*self.rels.step_input(step_node, input_node))

        # Step Outputs
        for out in step.get("outputs", []):
            output_node = self.nodes.build_node(workflow_id, step.get("step_id"), out.get("name", ""), out.get("description", ""))
            self.neo.merge_node(output_node["label"], output_node["properties"], unique_key="output_uid")
            self.neo.merge_rel(*self.rels.step_output(step_node, output_node))
