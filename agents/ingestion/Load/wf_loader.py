import pprint
import json
from tqdm import tqdm
from extract.parser import WorkflowParser
from extract.normalize import Normalizer
# from transform.wf_node_builder import NodeBuilder
from transform.node_builder import GenericNodeBuilder
from transform.wf_rel_builder import RelationshipBuilder
from transform.edge_builder import GenericRelationshipBuilder
from Load.neo4j_client import Neo4jClient
from config.schema_nodes import Category,CategoryProperties ,Workflow ,WorkflowProperties ,Input ,InputProperties ,Output ,OutputProperties
from config.schema_relationships import WorkflowCategory, WorkflowInput, WorkflowOutput
class GraphLoader:
    def __init__(self, neo4j: Neo4jClient):
        self.neo = neo4j
        self.parser = WorkflowParser()
        self.norm = Normalizer()
        self.nodes = GenericNodeBuilder()
        self.rels = GenericRelationshipBuilder()


    def import_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            workflows = json.load(f)
        print(f"🔍 Processing {len(workflows)} workflows... - wf_loader.py:25")
        for wf in tqdm(workflows, desc="Workflows", unit="wf"):
            self._process_workflow(wf)

    def _process_workflow(self, wf):
        # Category node

        category = Category(properties=CategoryProperties(name=wf.get("category")))
        print(category, "category - wf_loader.py:33")
        cat_node = self.nodes.build_node(category)
        print(cat_node, "node - wf_loader.py:35")
        self.neo.merge_node_2(cat_node)

        # Iterate workflow files
        for wf_file in wf.get("workflow_files", []):
            self._process_workflow_file(wf_file, wf, cat_node)

    def _process_workflow_file(self, wf_file, wf_root, cat_node):
        # -------------------------------
        # Build Workflow node
        # -------------------------------
        workflow_props = WorkflowProperties(
            name=wf_file["workflow_name"].strip(),
            category=cat_node["properties"]["name"],
            readme=wf_root.get("readme_content", ""),
            file_name=wf_file.get("file_name", ""),
            raw_download_url=wf_file.get("raw_download_url", ""),
            number_of_steps=wf_file.get("number_of_steps", 0),
            has_readme=wf_root.get("has_readme", False),
            has_changelog=wf_root.get("has_changelog", False),
            has_test_data=wf_root.get("has_test_data", False),
            workflow_repository=wf_file["workflow_name"].strip(),
        )
        workflow_node = self.nodes.build_node(Workflow(properties=workflow_props))
        self.neo.merge_node_2(workflow_node)

        # -------------------------------
        # Category → Workflow
        # -------------------------------
        cat_workflow_rel = WorkflowCategory(
            source=Workflow(properties=workflow_props),
            target=Category(properties=CategoryProperties(name=cat_node["properties"]["name"]))
        )
        rel_tuple = self.rels.build_edge(cat_workflow_rel)
        self.neo.merge_rel(*rel_tuple)

        # -------------------------------
        # Workflow Inputs / Outputs
        # -------------------------------
        inputs, outputs = self.parser.extract_io(wf_root.get("readme_content", ""))
        print(inputs, "inputs - wf_loader.py:75")
        print(outputs, "outputs - wf_loader.py:76")
        for inp in inputs:
            input_node_model = Input(properties=InputProperties(description=inp))
            input_node = self.nodes.build_node(input_node_model)
            self.neo.merge_node_2(input_node)

            wf_input_rel = WorkflowInput(
                source=Workflow(properties=workflow_props),
                target=Input(properties=InputProperties(description=inp))
            )
            rel_tuple = self.rels.build_edge(wf_input_rel)
            self.neo.merge_rel(*rel_tuple)

        for out in outputs:
            output_node_model = Output(properties=OutputProperties(description=out))
            output_node = self.nodes.build_node(output_node_model)
            self.neo.merge_node_2(output_node)

            wf_output_rel = WorkflowOutput(
                source=Workflow(properties=workflow_props),
                target=Output(properties=OutputProperties(description=out))
            )
            rel_tuple = self.rels.build_edge(wf_output_rel)
            self.neo.merge_rel(*rel_tuple)
