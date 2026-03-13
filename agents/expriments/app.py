
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import tempfile
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



import importlib.util
import types


workflow_gen_dir = os.path.join(expriments_root, "workflow_generator")
if workflow_gen_dir not in sys.path:
    sys.path.insert(0, workflow_gen_dir)

if expriments_root not in sys.path:
    sys.path.insert(0, expriments_root)

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


# Shared context setup function for all API end points
def get_workflow_context():
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

    return {
        "tool_map": tool_map,
        "model": model,
        "reverse_dict": reverse_dict,
        "forward_dict": forward_dict,
        "validator": validator,
    }

class WorkflowRequest(BaseModel):
    seed_tool: str
    max_steps: Optional[int] = 15


# Endpoint for transformer mode
@app.post("/generate-workflow-transformer")
def generate_workflow_transformer(req: WorkflowRequest):
    ctx = get_workflow_context()
    predicted_chain = workflow_gen.generate_tool_sequence(
        ctx["model"],
        ctx["forward_dict"],
        ctx["reverse_dict"],
        req.seed_tool,
        max_len=req.max_steps,
    )
    final_chain = ctx["validator"].validate_and_fix_chain(predicted_chain, ctx["tool_map"])
    return {"Generated Workflow": " -> ".join(final_chain)}

# Endpoint for hybrid mode
@app.post("/generate-workflow-hybrid")
def generate_workflow_hybrid(req: WorkflowRequest):
    ctx = get_workflow_context()
    predicted_chain, _ = workflow_gen.hybrid_generate_tool_sequence(
        model=ctx["model"],
        forward_dict=ctx["forward_dict"],
        reverse_dict=ctx["reverse_dict"],
        seed_tool_name=req.seed_tool,
        max_len=req.max_steps,
        top_k=8,
        top_p=0.9,
        temperature=1.0,
        repetition_penalty=1.1,
        use_llm=True,
        llm_model="gpt-4o-mini",
        llm_provider="auto",
        validator=ctx["validator"],
        return_trace=True,
    )
    final_chain = ctx["validator"].validate_and_fix_chain(predicted_chain, ctx["tool_map"])
    return {"Generated Workflow": " -> ".join(final_chain)}



class DownloadGARequest(BaseModel):
    """
    Request model for downloading .ga file.
    mode: 1 = transformer (default), 2 = hybrid
    """
    seed_tool: str
    max_steps: Optional[int] = 15
    mode: Optional[int] = 1  # 1 = transformer (default), 2 = hybrid
@app.post(
    "/download-workflow-ga",
    summary="Download Galaxy .ga workflow file",
    description="Generate and download a Galaxy workflow .ga file.\n\nmode: 1 = transformer (default), 2 = hybrid (transformer + LLM)."
)
def download_workflow_ga(req: DownloadGARequest):
    ctx = get_workflow_context()
    mode = "transformer" if req.mode == 1 else "hybrid"

    if mode == "hybrid":
        predicted_chain, _ = workflow_gen.hybrid_generate_tool_sequence(
            model=ctx["model"],
            forward_dict=ctx["forward_dict"],
            reverse_dict=ctx["reverse_dict"],
            seed_tool_name=req.seed_tool,
            max_len=req.max_steps,
            top_k=8,
            top_p=0.9,
            temperature=1.0,
            repetition_penalty=1.1,
            use_llm=True,
            llm_model="gpt-4o-mini",
            llm_provider="auto",
            validator=ctx["validator"],
            return_trace=True,
        )
    else:
        predicted_chain = workflow_gen.generate_tool_sequence(
            ctx["model"],
            ctx["forward_dict"],
            ctx["reverse_dict"],
            req.seed_tool,
            max_len=req.max_steps,
        )

    final_chain = ctx["validator"].validate_and_fix_chain(predicted_chain, ctx["tool_map"])
    workflow_json = workflow_gen.create_galaxy_workflow(
        final_chain,
        tool_mapping=ctx["tool_map"],
        workflow_name="AI_Validated_Workflow",
        validator=ctx["validator"],
    )

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ga", mode="w", encoding="utf-8") as tmpfile:
        json.dump(workflow_json, tmpfile, indent=4)
        tmpfile_path = tmpfile.name

    return FileResponse(
        tmpfile_path,
        media_type="application/json",
        filename="AI_Generated_workflow.ga",
        headers={"Content-Disposition": "attachment; filename=AI_Generated_workflow.ga"}
    )