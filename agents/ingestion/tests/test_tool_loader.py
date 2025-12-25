import sys
import pathlib
import pytest
from unittest.mock import MagicMock

# Ensure repo root is on sys.path so `agents` package imports resolve during tests
ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import importlib.util

# Load ToolLoader directly from file to avoid package import issues
cwd = pathlib.Path(__file__).resolve()
ROOT = None
for p in cwd.parents:
    if (p / "agents").exists():
        ROOT = p
        break
if ROOT is None:
    raise RuntimeError("Could not find repository root containing 'agents' directory")

tool_loader_path = ROOT / "agents" / "ingestion" / "Load" / "tool_loader.py"
spec = importlib.util.spec_from_file_location("tool_loader", str(tool_loader_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ToolLoader = mod.ToolLoader


class DummyNeo:
    def __init__(self):
        self.merged_nodes = []
        self.merged_rels = []

    def merge_node(self, label, properties, unique_key=None):
        self.merged_nodes.append((label, dict(properties), unique_key))

    def merge_rel(self, type, from_label, from_props, to_label, to_props, rel_props):
        self.merged_rels.append((type, from_label, from_props, to_label, to_props, rel_props))


def make_tool_dict():
    return {
        "id": "tool_x",
        "name": "Tool X",
        "description": "desc",
        "version": "1.2",
        "categories": ["Get Data"],
        "inputs": [{"name": "inputA", "type": "file", "accepts": ["txt"]}],
        "outputs": [{"name": "outA", "format": "csv"}],
        "help": ""
    }


def test_tool_loader_process_tool_creates_nodes_and_rels(tmp_path):
    neo = DummyNeo()
    # Instantiate ToolLoader without running its __init__ to avoid import
    # issues for package-relative imports during tests.
    tl = ToolLoader.__new__(ToolLoader)
    tl.neo = neo

    # Load builder classes directly from files
    import importlib.util
    node_builder_path = ROOT / "agents" / "ingestion" / "transform" / "tool_node_builder.py"
    rel_builder_path = ROOT / "agents" / "ingestion" / "transform" / "tool_rel_builder.py"

    spec_nb = importlib.util.spec_from_file_location("tool_node_builder", str(node_builder_path))
    mod_nb = importlib.util.module_from_spec(spec_nb)
    spec_nb.loader.exec_module(mod_nb)
    ToolMetadataBuilder = mod_nb.ToolMetadataBuilder

    spec_rb = importlib.util.spec_from_file_location("tool_rel_builder", str(rel_builder_path))
    mod_rb = importlib.util.module_from_spec(spec_rb)
    spec_rb.loader.exec_module(mod_rb)
    ToolMetadataRelations = mod_rb.ToolMetadataRelations

    tl.build = ToolMetadataBuilder()
    tl.rel = ToolMetadataRelations()

    t = make_tool_dict()

    # process single tool
    tl.process_tool(t)

    # Expect Tool node merged
    labels = [n[0] for n in neo.merged_nodes]
    assert "Tool" in labels

    # Expect ToolCategory node merged
    assert any(n[0] == "ToolCategory" for n in neo.merged_nodes)

    # Inputs and outputs merged
    assert any(n[0] == "ToolInput" for n in neo.merged_nodes)
    assert any(n[0] == "ToolOutput" for n in neo.merged_nodes)

    # Relationships created
    rel_types = [r[0] for r in neo.merged_rels]
    assert "BELONGS_TO" in rel_types
    assert "TOOL_HAS_INPUT" in rel_types
    assert "TOOL_HAS_OUTPUT" in rel_types
