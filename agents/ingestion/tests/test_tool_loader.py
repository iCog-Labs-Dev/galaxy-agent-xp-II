import sys
import pathlib
import pytest
from unittest.mock import MagicMock
import importlib.util

# Ensure repo root is on sys.path so `agents` package imports resolve during tests
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

# Load ToolLoader directly from file to avoid package import issues
tool_loader_path = ROOT / "agents" / "ingestion" / "Load" / "tool_loader.py"
spec = importlib.util.spec_from_file_location("tool_loader", str(tool_loader_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ToolLoader = mod.ToolLoader


class DummyNeo:
    """Mock Neo4j client for testing merge_node and merge_rel"""
    def __init__(self):
        self.merged_nodes = []
        self.merged_rels = []

    def merge_node(self, label, properties, unique_key=None):
        self.merged_nodes.append((label, dict(properties), unique_key))

    def merge_rel(self, type, from_label, from_props, to_label, to_props, rel_props=None):
        self.merged_rels.append((type, from_label, from_props, to_label, to_props, rel_props or {}))


def make_tool_dict(include_embedding=False):
    """Return a sample tool dictionary"""
    tool = {
        "id": "tool_x",
        "name": "Tool X",
        "description": "desc",
        "version": "1.2",
        "categories": ["Get Data"],
        "inputs": [{"name": "inputA", "type": "file", "accepts": ["txt"]}],
        "outputs": [{"name": "outA", "format": "csv"}],
        "help": ""
    }
    if include_embedding:
        tool["embedding"] = [0.1, 0.2, 0.3]
    return tool


def test_tool_loader_process_tool_creates_nodes_and_rels(tmp_path):
    """Test that ToolLoader processes a tool and creates expected nodes and relationships"""
    neo = DummyNeo()

    # Instantiate ToolLoader without running __init__ to avoid import issues
    tl = ToolLoader.__new__(ToolLoader)
    tl.neo = neo

    # Load builder classes dynamically
    node_builder_path = ROOT / "agents" / "ingestion" / "transform" / "tool_node_builder.py"
    rel_builder_path = ROOT / "agents" / "ingestion" / "transform" / "tool_rel_builder.py"

    # ToolMetadataBuilder
    spec_nb = importlib.util.spec_from_file_location("tool_node_builder", str(node_builder_path))
    mod_nb = importlib.util.module_from_spec(spec_nb)
    spec_nb.loader.exec_module(mod_nb)
    ToolMetadataBuilder = mod_nb.ToolMetadataBuilder

    # ToolMetadataRelations
    spec_rb = importlib.util.spec_from_file_location("tool_rel_builder", str(rel_builder_path))
    mod_rb = importlib.util.module_from_spec(spec_rb)
    spec_rb.loader.exec_module(mod_rb)
    ToolMetadataRelations = mod_rb.ToolMetadataRelations

    # Assign builders to ToolLoader instance
    tl.build = ToolMetadataBuilder()
    tl.rel = ToolMetadataRelations()

    # Create a test tool including embedding
    t = make_tool_dict(include_embedding=True)

    # Process the tool
    tl.process_tool(t)

    # Check Tool node merged
    tool_nodes = [n for n in neo.merged_nodes if n[0] == "Tool"]
    assert len(tool_nodes) == 1
    tool_node_props = tool_nodes[0][1]
    assert tool_node_props["tool_id"] == "tool_x"
    assert tool_node_props["name"] == "Tool X"
    # Embedding check
    assert "embedding" in tool_node_props
    assert tool_node_props["embedding"] == [0.1, 0.2, 0.3]

    # Check ToolCategory node merged
    assert any(n[0] == "ToolCategory" for n in neo.merged_nodes)

    # Check inputs and outputs merged
    assert any(n[0] == "ToolInput" for n in neo.merged_nodes)
    assert any(n[0] == "ToolOutput" for n in neo.merged_nodes)

    # Check relationships
    rel_types = [r[0] for r in neo.merged_rels]
    assert "BELONGS_TO" in rel_types
    # Adjusted to match actual rel names in code: HAS_INPUT / HAS_OUTPUT
    assert "HAS_INPUT" in rel_types
    assert "HAS_OUTPUT" in rel_types
