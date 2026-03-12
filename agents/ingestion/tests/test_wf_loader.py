import sys
import pathlib
import importlib.util
from agents.ingestion.Load.wf_loader import GraphLoader

# Ensure repo root is on sys.path so `agents` package imports resolve during tests
ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


cwd = pathlib.Path(__file__).resolve()
ROOT = None
for p in cwd.parents:
    if (p / "agents").exists():
        ROOT = p
        break
if ROOT is None:
    raise RuntimeError("Could not find repository root containing 'agents' directory")


class DummyNeo:
    def __init__(self):
        self.merged_nodes = []
        self.merged_rels = []

    def merge_node(self, label, properties, unique_key=None):
        self.merged_nodes.append((label, dict(properties), unique_key))

    def merge_rel(self, type, from_label, from_props, to_label, to_props, rel_props):
        self.merged_rels.append((type, from_label, from_props, to_label, to_props, rel_props))


def load_builder(module_path_parts, classname):
    import importlib.util
    node_builder_path = ROOT.joinpath(*module_path_parts)
    spec_nb = importlib.util.spec_from_file_location("nb", str(node_builder_path))
    mod_nb = importlib.util.module_from_spec(spec_nb)
    spec_nb.loader.exec_module(mod_nb)
    return getattr(mod_nb, classname)


def test_wf_loader_process_workflow_creates_nodes_and_rels():
    neo = DummyNeo()

    # Instantiate GraphLoader without running its __init__
    gl = GraphLoader.__new__(GraphLoader)
    gl.neo = neo

    # Load builders
    NodeBuilder = load_builder(["agents", "ingestion", "transform", "wf_node_builder.py"], "NodeBuilder")
    RelBuilder = load_builder(["agents", "ingestion", "transform", "wf_rel_builder.py"], "RelationshipBuilder")

    gl.nodes = NodeBuilder()
    gl.rels = RelBuilder()

    # stub normalizer and parser used by _process_workflow
    class DummyNorm:
        def normalize_category(self, c):
            return c.strip()

    class DummyParser:
        def extract_io(self, readme):
            return (["rw_input"], ["rw_output"])

    gl.norm = DummyNorm()
    gl.parser = DummyParser()

    # Prepare minimal workflow structure
    wf = {
        "category": "Get Data",
        "workflow_files": [
            {
                "workflow_name": "example/repo",
                "file_name": "wf.ga",
                "raw_download_url": "http://example.com/wf.ga",
                "number_of_steps": 1,
                "steps": [
                    {
                        "step_id": 10,
                        "name": "stepA",
                        "inputs": [{"name": "inA", "description": "descA"}],
                        "outputs": [{"name": "outA", "description": "descOutA"}],
                        "input_connections": {"inA": {"id": 1}},
                    }
                ]
            }
        ],
        "readme_content": "",
        "has_readme": True,
        "has_changelog": False,
        "has_test_data": False,
        "planemo_tests": []
    }

    # run processing of the workflow
    gl._process_workflow(wf)

    # Expect Category and Workflow nodes
    labels = [n[0] for n in neo.merged_nodes]
    assert "Category" in labels
    assert "Workflow" in labels

    # Expect Step node merged
    assert any(n[0] == "Step" for n in neo.merged_nodes)

    # Step input/output nodes merged
    assert any(n[0] == "Input" for n in neo.merged_nodes)
    assert any(n[0] == "Output" for n in neo.merged_nodes)

    # Relationships include HAS_WORKFLOW, HAS_STEP and step IO relations and README IO relations
    rel_types = [r[0] for r in neo.merged_rels]
    assert "HAS_WORKFLOW" in rel_types
    assert "HAS_STEP" in rel_types
    assert "STEP_REQUIRES" in rel_types
    assert "STEP_GENERATES" in rel_types
    assert "REQUIRES" in rel_types  # workflow-level readme input
    assert "GENERATES" in rel_types  # workflow-level readme output
