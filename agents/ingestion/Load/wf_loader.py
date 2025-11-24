from extract.parser import WorkflowParser
from extract.normalize import Normalizer
from transform.wf_node_builder import NodeBuilder
from transform.wf_rel_builder import RelationshipBuilder
from Load.neo4j_client import Neo4jClient
import json

class GraphLoader:
    def __init__(self, neo4j: Neo4jClient):
        self.neo = neo4j
        self.parser = WorkflowParser()
        self.norm = Normalizer()
        self.nodes = NodeBuilder()
        self.rels = RelationshipBuilder()

    def import_file(self, path):
        with open(path) as f:
            workflows = json.load(f)

        for wf in workflows:
            self.process_workflow(wf)

    def process_workflow(self, wf):
        # Workflow
        wf_node = self.nodes.create_workflow(wf)
        self.neo.merge_node(wf_node["label"], wf_node["properties"])

        # Category
        cat_name = self.norm.normalize_category(wf["category"])
        cat_node = self.nodes.create_category(cat_name)
        self.neo.merge_node(cat_node["label"], cat_node["properties"])

        # Relation category → workflow
        self.neo.merge_rel(
            "HAS_WORKFLOW",
            "Category", cat_node["properties"],
            "Workflow", wf_node["properties"],
            {}
        )

        # Tools
        for step, tool in enumerate(wf["tool_names"], start=1):
            clean_tool = self.norm.normalize_tool(tool)
            tool_node = self.nodes.create_tool(clean_tool)
            self.neo.merge_node(tool_node["label"], tool_node["properties"])

            # Relation
            self.neo.merge_rel(
                "USES_TOOL",
                "Workflow", wf_node["properties"],
                "Tool", tool_node["properties"],
                {"step": step}
            )

        # IO extraction
        inputs, outputs = self.parser.extract_io(wf["readme_cleaned"])

        for inp in inputs:
            i_node = self.nodes.create_io_node("Input", inp)
            self.neo.merge_node(i_node["label"], i_node["properties"])
            self.neo.merge_rel(
                "REQUIRES",
                "Workflow", wf_node["properties"],
                "Input", i_node["properties"],
                {}
            )

        for out in outputs:
            o_node = self.nodes.create_io_node("Output", out)
            self.neo.merge_node(o_node["label"], o_node["properties"])
            self.neo.merge_rel(
                "GENERATES",
                "Workflow", wf_node["properties"],
                "Output", o_node["properties"],
                {}
            )
