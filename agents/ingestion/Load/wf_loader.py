import pprint
import time
import json
from tqdm import tqdm
from extract.parser import WorkflowParser
from extract.normalize import Normalizer
# from transform.wf_node_builder import NodeBuilder
from transform.node_builder import GenericNodeBuilder
from transform.wf_rel_builder import RelationshipBuilder
from transform.edge_builder import GenericRelationshipBuilder
from Load.neo4j_client import Neo4jClient
from config.schema_nodes import Category,CategoryProperties ,Workflow ,WorkflowProperties ,Input ,InputProperties ,Output ,OutputProperties, Step, StepProperties, Tool, ToolProperties
from config.schema_relationships import WorkflowCategory, WorkflowInput, WorkflowOutput, WorkflowStep, StepTool, StepInput, StepOutput, OutputInput

class GraphLoader:
    def __init__(self, neo4j: Neo4jClient):
        self.neo = neo4j
        self.parser = WorkflowParser()
        self.norm = Normalizer()
        self.nodes = GenericNodeBuilder()
        self.rels = GenericRelationshipBuilder()
        
        self.local_nodes = {}  # key = node_id, value = node dict
        self.local_rels = []   # list of tuples from build_edge()

    def _store_node(self, node):
        self.local_nodes[node["properties"]["id"]] = node

    def _store_rel(self, rel_tuple):
        self.local_rels.append(rel_tuple)

    # -----------------------------
    # Push local graph to Neo4j
    # -----------------------------
    def flush_to_neo4j(self, batch_size=100):
        # Merge nodes in batches
        nodes = list(self.local_nodes.values())
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i+batch_size]
            self.neo.merge_nodes_batch(batch)

        # Merge relationships in batches
        rels = self.local_rels
        for i in range(0, len(rels), batch_size):
            batch = rels[i:i+batch_size]
            self.neo.merge_rels_batch(batch)
        
        # Clear local storage        
        self.local_nodes.clear()
        self.local_rels.clear()


    def import_file(self, path):
        with open(path, "r", encoding="utf-8") as f:
            workflows = json.load(f)
        print(f"🔍 Processing {len(workflows)} workflows... - wf_loader.py:56")
        for wf in tqdm(workflows, desc="Workflows", unit="wf"):
            self._process_workflow(wf)
        # flush all nodes and relationships in batch
        print("\n🔄 Flushing local graph to Neo4j... - wf_loader.py:60")
        start_time = time.time()

        # Using tqdm just for the sake of showing progress if needed
        # Here, we can show a single progress bar for the flush
        with tqdm(total=1, desc="Flushing", unit="batch") as pbar:
            self.flush_to_neo4j()
            pbar.update(1)

        elapsed = time.time() - start_time
        print(f"✅ Flush completed in {elapsed:.2f}s - wf_loader.py:70")

    def _process_workflow(self, wf):
        # Category node

        category = Category(properties=CategoryProperties(name=wf.get("category")))
        print(category, "category - wf_loader.py:76")
        cat_node = self.nodes.build_node(category)
        print(cat_node, "node - wf_loader.py:78")
        self._store_node(cat_node)

        # Iterate workflow files
        for wf_file in wf.get("workflow_files", []):
            self._process_workflow_file(wf_file, wf, cat_node)
        
    # After processing all workflows, flush to Neo4j
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
        self._store_node(workflow_node)

        # -------------------------------
        # Category → Workflow
        # -------------------------------
        cat_workflow_rel = WorkflowCategory(
            source=Workflow(properties=workflow_props),
            target=Category(properties=CategoryProperties(name=cat_node["properties"]["name"]))
        )
        rel_tuple = self.rels.build_edge(cat_workflow_rel)
        self._store_rel(rel_tuple)

        # Steps
        for step in wf_file.get("steps", []):
            self._process_step(workflow_node, step)
    
    def _process_step(self, workflow_node, step: dict):
        """
        Build:
        - Step node
        - Input ports (declared + implied by wiring)
        - Output ports
        - FEEDS edges (dataflow wiring)
        """

        # -----------------------------------------
        # STEP 0 — Build Step UID
        # -----------------------------------------
        step_id = step["step_id"]
        step_uid = f"{workflow_node["properties"]["id"]}_{step_id}"

        # -----------------------------------------
        # STEP 1 — Create the Step node
        # -----------------------------------------
        step_props = StepProperties(
            step_uid=step_uid,
            step_id=step_id,
            name=step.get("name", ""),
            type=step.get("type", ""),
            annotation=step.get("annotation", "")
        )
        step_node = self.nodes.build_node(Step(properties=step_props))
        self._store_node(step_node)

        # Relationship: workflow → step
        wf_step_rel = WorkflowStep(
            source=workflow_node,
            target=Step(properties=step_props)
        )
        rel_tuple = self.rels.build_edge(wf_step_rel)
        self._store_rel(rel_tuple)

        # -----------------------------------------
        # STEP 2 — INPUT PORTS (declared + wired)
        # -----------------------------------------
        declared_ports = {inp.get("name", "") for inp in step.get("inputs", [])}
        wired_ports = set(step.get("input_connections", {}).keys())
        all_ports = declared_ports | wired_ports

        input_nodes = {}  # cache for wiring step

        for port_name in all_ports:

            input_uid = f"{step_uid}_{port_name}"

            input_props = InputProperties(
                description=port_name,
                input_uid=input_uid
            )
            input_node = self.nodes.build_node(Input(properties=input_props))
            self._store_node(input_node)

            input_nodes[port_name] = input_node

            # Step -> InputPort
            step_input_rel = StepInput(
                source=Step(properties=step_props),
                target=Input(properties=input_props)
            )
            rel_tuple = self.rels.build_edge(step_input_rel)
            self._store_rel(rel_tuple)

        # -----------------------------------------
        # STEP 3 — OUTPUT PORTS
        # -----------------------------------------
        output_nodes = {}  # cache for wiring

        for out in step.get("outputs", []):
            out_name = out.get("name", "")
            output_uid = f"{step_uid}_{out_name}"

            output_props = OutputProperties(
                description=out_name,
                output_uid=output_uid
            )
            output_node = self.nodes.build_node(Output(properties=output_props))
            self._store_node(output_node)

            output_nodes[out_name] = output_node

            # Step -> OutputPort
            step_output_rel = StepOutput(
                source=Step(properties=step_props),
                target=Output(properties=output_props)
            )
            rel_tuple = self.rels.build_edge(step_output_rel)
            self._store_rel(rel_tuple)

        # -----------------------------------------
        # STEP 4 — DATAFLOW / WIRING (FEEDS edges)
        # -----------------------------------------
        for port_name, conn in step.get("input_connections", {}).items():
            upstream_step_id = conn["id"]
            upstream_output_name = conn["output_name"]

            # Build upstream OutputPort UID
            upstream_step_uid = f"{workflow_node["properties"]["id"]}_{upstream_step_id}"
            upstream_output_uid = f"{upstream_step_uid}_{upstream_output_name}"

            # Create upstream Output node (must exist)
            upstream_output_props = OutputProperties(
                description=upstream_output_name,
                output_uid=upstream_output_uid
            )
            upstream_output_node = self.nodes.build_node(Output(properties=upstream_output_props))
            self._store_node(upstream_output_node)

            # Locate downstream INPUT port (created in section 2)
            downstream_input_node = input_nodes[port_name]
            print("port_name: - wf_loader.py:232", port_name)
            # Create FEEDS relationship (Output → Input)
            feeds_rel = OutputInput(
                source=upstream_output_node,
                target=downstream_input_node,
                properties={"port": port_name}
            )
            rel_tuple = self.rels.build_edge(feeds_rel)
            print("rel_tuple - wf_loader.py:240",rel_tuple)
            self._store_rel(feeds_rel)

        # for port_name, conn in step.get("input_connections", {}).items():

        #     upstream_step_id = conn["id"]
        #     upstream_output_name = conn["output_name"]

        #     # Build upstream OutputPort UID
        #     upstream_step_uid = f"{workflow_node["properties"]["id"]}_{upstream_step_id}"
        #     upstream_output_uid = f"{upstream_step_uid}_{upstream_output_name}"

        #     # Upstream OUTPUT port node
        #     upstream_output_props = OutputProperties(
        #         description=upstream_output_name,
        #         output_uid=upstream_output_uid
        #     )
        #     upstream_output_node = self.nodes.build_node(Output(properties=upstream_output_props))
        #     self.neo.merge_node_2(upstream_output_node)   # must exist for wiring

        #     # Downstream INPUT port node
        #     downstream_input_node = input_nodes[port_name]

        #     # Connect upstream OUTPUT → downstream INPUT
        #     self.neo.merge_rel(
        #         upstream_output_node,
        #         "FEEDS",
        #         downstream_input_node,
        #         properties={"port": port_name}
        #     )

        # return step_node

    # def _process_step(self, step, workflow_node, workflow_props):
    #         # 1 — Build Step node
    #         step_uid = f"{workflow_props.workflow_repository}_{step['step_id']}"
    #         step_props = StepProperties(
    #             step_uid=step_uid,
    #             step_id=step["step_id"],
    #             name=step.get("name", ""),
    #             type=step.get("type", ""),
    #             annotation=step.get("annotation", "")
    #         )
    #         step_node = self.nodes.build_node(Step(properties=step_props))
    #         self._store_node(step_node)

    #         # Workflow → Step relationship
    #         workflow_step_rel = WorkflowStep(
    #             source=Workflow(properties=workflow_props),
    #             target=Step(properties=step_props)
    #         )
    #         rel_tuple = self.rels.build_edge(workflow_step_rel)
    #         self._store_rel(rel_tuple)

    #         # 2 — Tool (if applicable)
    #         if step.get("type") == "tool" and step.get("tool_id"):
    #             tool_props = ToolProperties(
    #                 name=step["tool_id"],
    #                 version=step.get("tool_version", ""),
    #                 description=step.get("annotation", ""),
    #                 help=step.get("help", "")
    #             )
    #             tool_node = self.nodes.build_node(Tool(properties=tool_props))
    #             self._store_node(tool_node)

    #             # Step → Tool relationship
    #             step_tool_rel = StepTool(
    #                 source=Step(properties=step_props),
    #                 target=Tool(properties=tool_props)
    #             )
    #             rel_tuple = self.rels.build_edge(step_tool_rel)
    #             self._store_rel(rel_tuple)

    #         # Step Inputs
    #         for inp in step.get("inputs", []):
    #             input_props = InputProperties(
    #                 description= inp.get("description", ""),
    #                 input_uid= f"{step_uid}_{inp.get('name', '')}"
    #             )
                
    #             input_node = self.nodes.build_node(Input(properties=input_props))
    #             self._store_node(input_node)

    #             step_input_rel = StepInput(
    #                 source=Step(properties=step_props),
    #                 target=Input(properties=input_props)
    #             )
    #             rel_tuple = self.rels.build_edge(step_input_rel)
    #             self._store_rel(rel_tuple)

    #         # 3 — Step Outputs
    #         for out in step.get("outputs", []):
    #             output_props = OutputProperties(
    #                 description=out.get("description", ""),
    #                 output_uid=f"{step_uid}_{out.get('name', '')}"
    #             )
    #             output_node = self.nodes.build_node(Output(properties=output_props))
    #             self._store_node(output_node)

    #             step_output_rel = StepOutput(
    #                 source=Step(properties=step_props),
    #                 target=Output(properties=output_props)
    #             )
    #             rel_tuple = self.rels.build_edge(step_output_rel)
    #             self._store_rel(rel_tuple)
            
    #         # 4 — Dataflow edges
    #         for port_name, conn in step.get("input_connections", {}).items():
    #             upstream_step_id = conn["id"]
    #             upstream_output_name = conn["output_name"]

    #             # Create the upstream Output node
    #             upstream_output_model = Output(
    #                 properties=OutputProperties(description=upstream_output_name)
    #             )
    #             upstream_output_node = self.nodes.build_node(upstream_output_model)
    #             self.neo.merge_node_2(upstream_output_node)

    #             # Link output → downstream step
    #             self.neo.merge_rel(
    #                 upstream_output_node,
    #                 "FEEDS",
    #                 step_node,
    #                 properties={"port": port_name}
    #             )

