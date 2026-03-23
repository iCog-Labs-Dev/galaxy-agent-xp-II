


# --- Imports ---
import os
import sys
import json
import datetime
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

# --- Path Setup (for local imports) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
expriments_root = os.path.abspath(current_dir)
scripts_path = os.path.join(expriments_root, "scripts")
for path in [project_root, expriments_root, scripts_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

import threading
from agents.suggesting_agent import ToolSuggestionAgent
from agents.expriments.workflow_generator.utils import extract_short_name_from_id

# --- Environment ---
load_dotenv()

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
expriments_root = os.path.abspath(current_dir)
scripts_path = os.path.join(expriments_root, "scripts")

for path in [project_root, expriments_root, scripts_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

workflow_utils_path = os.path.join(current_dir, "workflow_generator")
if workflow_utils_path not in sys.path:
    sys.path.append(workflow_utils_path)
import utils

# --- Dynamic Import ---
import importlib.util
workflow_gen_dir = os.path.join(expriments_root, "workflow_generator")
if workflow_gen_dir not in sys.path:
    sys.path.insert(0, workflow_gen_dir)
workflow_gen_path = os.path.join(expriments_root, "workflow_generator", "run_workflow_generator.py")
spec = importlib.util.spec_from_file_location("run_workflow_generator", workflow_gen_path)
workflow_gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow_gen)

# --- FastAPI App ---
app = FastAPI()
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



# --- Shared workflow context loaded once at startup ---
def _load_workflow_context():
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

# Global shared workflow context
_workflow_context = _load_workflow_context()

def get_workflow_context():
    return _workflow_context

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
        workflow_name="AI_Validated_Workflow"
    )

    # Set workflow version and LLM-generated name using Gemini
    workflow_version = workflow_json.get("format-version", "1.0")
    workflow_json["workflow-version"] = workflow_version

    llm_name = utils.generate_workflow_name_llm(workflow_json)
    workflow_json["name"] = llm_name

    # Build filename: {llm_name}_v{version}_{timestamp}.ga
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{llm_name}_v{workflow_version}_{timestamp}.ga"

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ga", mode="w", encoding="utf-8") as tmpfile:
        json.dump(workflow_json, tmpfile, indent=4)
        tmpfile_path = tmpfile.name

    return FileResponse(
        tmpfile_path,
        media_type="application/json",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



_integration_lock = threading.Lock()
_integration_agent = None
_integration_tool_id_dict = None
_integration_metadata = None
_integration_agent_error = None
def _load_integration_resources():
    global _integration_agent, _integration_tool_id_dict, _integration_metadata, _integration_agent_error
    try:
        if _integration_agent is None:
            _integration_agent = ToolSuggestionAgent()
        if _integration_tool_id_dict is None:
            tool_id_dict_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'agents', 'data', 'tool_id_dict.txt')
            with open(tool_id_dict_path, 'r') as f:
                _integration_tool_id_dict = json.load(f)
        if _integration_metadata is None:
            with open(_integration_agent.metadata_path, 'r', encoding='utf-8') as f:
                _integration_metadata = json.load(f)
    except Exception as e:
        _integration_agent_error = str(e)

_load_integration_resources()


class IntegrationRequest(BaseModel):
    query: str
    max_steps: Optional[int] = 15


@app.post("/Generating-Workflow-from-Query")
def integrated_workflow(req: IntegrationRequest):
    if _integration_agent_error:
        raise HTTPException(status_code=500, detail=f"Integration agent/model load error: {_integration_agent_error}")
    with _integration_lock:
        agent = _integration_agent
        tool_id_dict = _integration_tool_id_dict
        # Step 1: Get tool recommendations (top_k always 5)
        suggestions = agent.suggest_tools(req.query, 5)
        if not suggestions:
            raise HTTPException(status_code=404, detail="No tools found for query.")
        # Step 2: Find valid seed tool (short name in tool_id_dict)
        seed_short_name = None
        for tool in suggestions:
            short_name = extract_short_name_from_id(tool['id'])
            if short_name in tool_id_dict:
                seed_short_name = short_name
                break
        if not seed_short_name:
            raise HTTPException(status_code=400, detail="No recommended tool found in tool_id_dict.")
        # Step 3: Generate workflow (hybrid mode)
        ctx = get_workflow_context()
        predicted_chain, _ = workflow_gen.hybrid_generate_tool_sequence(
            model=ctx["model"],
            forward_dict=ctx["forward_dict"],
            reverse_dict=ctx["reverse_dict"],
            seed_tool_name=seed_short_name,
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
        return {
            "query": req.query,
            "recommended_tool": seed_short_name,
            "workflow": " -> ".join(final_chain)
        }
