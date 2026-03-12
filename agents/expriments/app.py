from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
import sys

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
expriments_root = os.path.abspath(current_dir)
scripts_path = os.path.join(expriments_root, "scripts")

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if expriments_root not in sys.path:
    sys.path.insert(0, expriments_root)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


# Import the main logic from run_workflow_generator.py
import importlib.util
import types

# Ensure workflow_generator is in sys.path for relative imports to work
workflow_gen_dir = os.path.join(expriments_root, "workflow_generator")
if workflow_gen_dir not in sys.path:
    sys.path.insert(0, workflow_gen_dir)
# Also ensure expriments_root is in sys.path for package imports
if expriments_root not in sys.path:
    sys.path.insert(0, expriments_root)
# Dynamically import the run_workflow_generator module
workflow_gen_path = os.path.join(expriments_root, "workflow_generator", "run_workflow_generator.py")
spec = importlib.util.spec_from_file_location("run_workflow_generator", workflow_gen_path)
workflow_gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow_gen)

app = FastAPI()

# --- CONFIGURATION ---
MODEL_PATH = os.getenv(
    "WORKFLOW_GENERATOR_MODEL_PATH",
    os.path.join(expriments_root, "transformer_model", "model_feb_28_26.h5")
)
BRIDGE_DICT_PATH = os.getenv(
    "WORKFLOW_GENERATOR_BRIDGE_DICT_PATH",
    os.path.join(expriments_root, "data", "tool_id_dict.txt")
)
TOOLS_CACHE_PATH = os.getenv(
    "WORKFLOW_GENERATOR_TOOLS_CACHE_PATH",
    os.path.join(expriments_root, "reports", "workflow_generator", "installed_tools_cache.json")
)


# Use the same argument names as in run_workflow_generator.py
class WorkflowRequest(BaseModel):
    seed_tool: str
    max_steps: Optional[int] = 15


# Endpoint for transformer mode
@app.post("/generate-workflow-transformer")
def generate_workflow_transformer(req: WorkflowRequest):
    tool_map = {}
    if os.path.exists(BRIDGE_DICT_PATH):
        with open(BRIDGE_DICT_PATH, 'r') as f:
            tool_map = json.load(f)

    model_manager = workflow_gen.ModelManager(MODEL_PATH)
    model_manager.load()
    model = model_manager.get_model()
    reverse_dict, forward_dict, class_weights = model_manager.get_metadata()

    GALAXY_URL = os.getenv("GALAXY_URL", "http://localhost:8080")
    API_KEY = os.getenv("GALAXY_API_KEY")
    validator = workflow_gen.GalaxyValidator(
        GALAXY_URL,
        API_KEY,
        timeout=15,
        skip_validation=False,
        cache_file=TOOLS_CACHE_PATH,
        cache_ttl=1800,
    )

    predicted_chain = workflow_gen.generate_tool_sequence(
        model,
        forward_dict,
        reverse_dict,
        req.seed_tool,
        max_len=req.max_steps,
    )
    final_chain = validator.validate_and_fix_chain(predicted_chain, tool_map)
    return {"Generated Workflow": " -> ".join(final_chain)}

