import sys
import pathlib
import importlib.util
import json
import hashlib


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

node_builder_path = ROOT / "agents" / "ingestion" / "transform" / "wf_node_builder.py"
spec = importlib.util.spec_from_file_location("wf_node_builder", str(node_builder_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NodeBuilder = mod.NodeBuilder


def test_create_workflow_and_step_serialization():
    nb = NodeBuilder()
    wf_data = {
        "workflow_repository": "example/repo",
        "file_name": "workflow.ga",
        "category": "Get Data",
        "raw_download_url": "http://example.com/wf.ga",
        "number_of_steps": 2,
        "readme": "",
        "has_readme": False,
    }

    wf_node = nb.create_workflow(wf_data)
    assert wf_node["label"] == "Workflow"
    assert "workflow_id" in wf_node["properties"]
    assert wf_node["properties"]["name"] == wf_data["workflow_repository"]

    workflow_id = wf_node["properties"]["workflow_id"]

    # Step with nested input_connections must be serialized to JSON string
    step = {
        "step_id": 1,
        "name": "step_one",
        "type": "tool",
        "annotation": "annot",
        "tool_id": "tool_x",
        "tool_version": "1.0",
        "input_connections": {"input_file": {"id": 32, "output_name": "hap1_contigs"}},
        "tool_shed_repository": {"owner": "alice", "name": "repo", "tool_shed": "shed"}
    }

    step_node = nb.create_step(step, workflow_id)
    assert step_node["label"] == "Step"
    props = step_node["properties"]
    # input_connections stored as JSON string
    assert isinstance(props.get("input_connections"), str)
    assert json.loads(props.get("input_connections")) == step["input_connections"]

    # step_uid deterministic: md5(workflow_id + '_' + step_id)
    expected = hashlib.md5((str(workflow_id) + "_" + str(step.get("step_id"))).encode("utf-8")).hexdigest()
    assert props.get("step_uid") == expected

