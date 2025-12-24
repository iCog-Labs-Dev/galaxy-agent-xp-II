import json
from tqdm import tqdm
from agents.ingestion.transform.wf_node_builder import NodeBuilder
from agents.ingestion.transform.wf_rel_builder import RelationshipBuilder
from agents.ingestion.Load.neo4j_client import Neo4jClient
from agents.ingestion.extract.parser import WorkflowParser

class WorkflowLoader:
    def __init__(self, neo: Neo4jClient, embeddings_path: str = None):
        self.neo = neo
        self.nodes = NodeBuilder()
        self.rels = RelationshipBuilder()
        self.parser = WorkflowParser()
        self.stats = {
            "workflows": 0,
            "workflow_files": 0,
            "steps": 0,
            "tools": 0,
            "inputs": 0,
            "outputs": 0
        }
        self.embeddings_map = {}
        if embeddings_path:
            self._load_embeddings(embeddings_path)

    def _load_embeddings(self, embeddings_path: str):
        try:
            with open(embeddings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                repo = item.get("workflow_repository")
                embedding = item.get("embedding")
                if repo and embedding:
                    self.embeddings_map[repo] = embedding
            print(f"📥 Loaded {len(self.embeddings_map)} embeddings from {embeddings_path}")
        except FileNotFoundError:
            print(f"⚠️ Embeddings file not found: {embeddings_path}")
        except Exception as e:
            print(f"⚠️ Error loading embeddings: {e}")

    def import_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            workflows = json.load(f)
        for wf in tqdm(workflows, desc="Inserting workflows", unit="workflow"):
            try:
                self.process_workflow(wf)
            except Exception as e:
                print(f"[wf_loader] error processing workflow {wf.get('workflow_repository')}: {e}")

        # Print stats
        print(f"\n📊 Workflow Stats:")
        for k, v in self.stats.items():
            print(f"  {k.capitalize()}: {v}")

    def process_workflow(self, wf: dict):
        self.stats["workflows"] += 1
        category_node = self.nodes.create_category(wf.get("category", "Unknown"))
        self.neo.merge_node("Category", category_node["properties"], "category_id")

        repo = wf.get("workflow_repository")
        embedding = wf.get("embedding") or self.embeddings_map.get(repo)
        readme = wf.get("readme_content") or wf.get("readme_cleaned") or wf.get("readme", "")
        inputs, outputs = self.parser.extract_io(readme)

        root_node = self.nodes.create_workflow(
            name=repo,
            category=category_node["properties"]["name"],
            root=True,
            readme=readme,
            embedding=embedding
        )
        self.neo.merge_node("Workflow", root_node["properties"], "workflow_id")
        self.neo.merge_rel(*self.rels.workflow_category(root_node, category_node))

        workflow_id = root_node["properties"]["workflow_id"]
        # Workflow-level inputs/outputs
        for inp in inputs:
            inp_node = self.nodes.create_workflow_input(workflow_id, inp)
            self.neo.merge_node("WorkflowInput", inp_node["properties"], "input_id")
            self.neo.merge_rel(*self.rels.workflow_input_semantic(root_node, inp_node))
            self.stats["inputs"] += 1
        for out in outputs:
            out_node = self.nodes.create_workflow_output(workflow_id, out)
            self.neo.merge_node("WorkflowOutput", out_node["properties"], "output_id")
            self.neo.merge_rel(*self.rels.workflow_output_semantic(root_node, out_node))
            self.stats["outputs"] += 1

        for wf_file in wf.get("workflow_files", []):
            self.process_workflow_file(root_node, wf_file, category_node)

    def process_workflow_file(self, root_node: dict, wf_file: dict, category_node: dict):
        self.stats["workflow_files"] += 1
        readme = wf_file.get("readme_content") or wf_file.get("readme", "")
        inputs, outputs = self.parser.extract_io(readme)

        file_node = self.nodes.create_workflow(
            name=wf_file.get("workflow_name", "Unknown"),
            category=category_node["properties"]["name"],
            root=False,
            file_name=wf_file.get("file_name"),
            download_url=wf_file.get("raw_download_url"),
            number_of_steps=wf_file.get("number_of_steps"),
            readme=readme
        )
        self.neo.merge_node("Workflow", file_node["properties"], "workflow_id")
        self.neo.merge_rel(*self.rels.workflow_category(file_node, category_node))
        self.neo.merge_rel(
            "HAS_IMPLEMENTATION",
            "Workflow", {"workflow_id": root_node["properties"]["workflow_id"]},
            "Workflow", {"workflow_id": file_node["properties"]["workflow_id"]}
        )

        workflow_id = file_node["properties"]["workflow_id"]
        # Workflow-file level inputs/outputs
        for inp in inputs:
            inp_node = self.nodes.create_workflow_input(workflow_id, inp)
            self.neo.merge_node("WorkflowInput", inp_node["properties"], "input_id")
            self.neo.merge_rel(*self.rels.workflow_input_semantic(file_node, inp_node))
            self.stats["inputs"] += 1
        for out in outputs:
            out_node = self.nodes.create_workflow_output(workflow_id, out)
            self.neo.merge_node("WorkflowOutput", out_node["properties"], "output_id")
            self.neo.merge_rel(*self.rels.workflow_output_semantic(file_node, out_node))
            self.stats["outputs"] += 1

        steps = wf_file.get("steps", [])
        self.stats["steps"] += len(steps)
        for step in steps:
            step_node = self.nodes.create_step(step, workflow_id)
            self.neo.merge_node("Step", step_node["properties"], "step_uid")
            self.neo.merge_rel(*self.rels.workflow_step(file_node, step_node))

            if step.get("tool_id"):
                self.stats["tools"] += 1
                tool_props = {"tool_id": step["tool_id"], "name": step.get("tool_name") or step["tool_id"]}
                self.neo.merge_node("Tool", tool_props, "tool_id")
                self.neo.merge_step_tool(step_node["properties"], tool_props)

            # Step inputs/outputs
            for inp in step.get("inputs", []):
                inp_node = self.nodes.create_input(workflow_id, step_node["properties"]["step_uid"], inp.get("name", ""), inp.get("description", ""))
                self.neo.merge_node("ToolInput", inp_node["properties"], "input_uid")
                self.neo.merge_rel(*self.rels.step_input(step_node, inp_node))
                self.neo.merge_rel(*self.rels.workflow_input(file_node, inp_node))
                self.stats["inputs"] += 1

            for out in step.get("outputs", []):
                out_node = self.nodes.create_output(workflow_id, step_node["properties"]["step_uid"], out.get("name", ""), out.get("description", ""))
                self.neo.merge_node("ToolOutput", out_node["properties"], "output_uid")
                self.neo.merge_rel(*self.rels.step_output(step_node, out_node))
                self.neo.merge_rel(*self.rels.workflow_output(file_node, out_node))
                self.stats["outputs"] += 1
