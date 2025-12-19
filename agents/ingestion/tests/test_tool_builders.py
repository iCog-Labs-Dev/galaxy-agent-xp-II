import sys
import pathlib
import pytest

# Ensure repo root is on sys.path so `agents` package imports resolve during tests
ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import importlib.util

# Load module directly from file so tests do not rely on package import paths
# Find repo root by searching upward for a directory that contains `agents`
cwd = pathlib.Path(__file__).resolve()
ROOT = None
for p in cwd.parents:
    if (p / "agents").exists():
        ROOT = p
        break
if ROOT is None:
    raise RuntimeError("Could not find repository root containing 'agents' directory")

tool_node_path = ROOT / "agents" / "ingestion" / "transform" / "tool_node_builder.py"
spec = importlib.util.spec_from_file_location("tool_node_builder", str(tool_node_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ToolMetadataBuilder = mod.ToolMetadataBuilder


def test_build_tool_basic():
    b = ToolMetadataBuilder()
    tool = {
        "id": "t1",
        "name": "MyTool",
        "description": "does X",
        "version": "0.1",
        "help": "usage"
    }

    node = b.build_tool(tool)
    assert node["label"] == "Tool"
    props = node["properties"]
    assert props["tool_id"] == "t1"
    assert props["name"] == "MyTool"
    assert props["description"] == "does X"
    assert props["version"] == "0.1"


def test_build_category_and_io_nodes():
    b = ToolMetadataBuilder()
    cat = b.build_category("Get Data")
    assert cat["label"] == "ToolCategory"
    assert cat["properties"]["category_id"] == "get-data"

    inp = {"name": "input1", "type": "file", "accepts": ["txt", "csv"]}
    in_node = b.build_input_node("t1", inp)
    assert in_node["label"] == "ToolInput"
    assert in_node["properties"]["input_uid"].startswith("t1::input::input1")
    assert "txt" in in_node["properties"]["accepts"]

    out = {"name": "out1", "format": "fasta"}
    out_node = b.build_output_node("t1", out)
    assert out_node["label"] == "ToolOutput"
    assert out_node["properties"]["output_uid"].startswith("t1::output::out1")
    assert out_node["properties"]["format"] == "fasta"
def test_tool_embedding_included():
    b = ToolMetadataBuilder()
    tool = {
        "id": "t2",
        "name": "EmbedTool",
        "description": "embeds X",
        "version": "0.2",
        "help": "usage",
        "embedding": [0.1, 0.2, 0.3]  # simulated embedding
    }
    node = b.build_tool(tool)
    props = node["properties"]
    assert "embedding" in props
    assert props["embedding"] == [0.1, 0.2, 0.3]