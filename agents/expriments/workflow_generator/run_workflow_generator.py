

import os
import sys
import json
import numpy as np
import tensorflow as tf
import h5py

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
from dotenv import load_dotenv
scripts_path = os.path.join(project_root, "scripts")


if project_root not in sys.path:
    sys.path.append(project_root)
if scripts_path not in sys.path:
    sys.path.append(scripts_path)


# --- IMPORTS ---
from agents.expriments.Next_Tool_Recommendation.model import build_transformer_model, ModelManager
from .generator import generate_tool_sequence
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
load_dotenv(os.path.join(project_root, '.env'))
from .generate_ga_file import create_galaxy_workflow
from .validator import GalaxyValidator

# --- CONFIGURATION ---
MODEL_PATH = os.path.join(project_root, "transformer_model", "model_feb_28_26.h5")
BRIDGE_DICT_PATH = os.path.join(project_root, "/home/henok/Desktop/galaxy/galaxy-agent-xp-II/agents/data/tool_id_dict.txt")

SEED_TOOL = "Grep1"
MAX_STEPS = 9


def main():
    print("🚀 Initializing Workflow Generator...")

    # 1. Load the Bridge Dictionary (Local Source of Truth)
    tool_map = {}
    if os.path.exists(BRIDGE_DICT_PATH):
        with open(BRIDGE_DICT_PATH, 'r') as f:
            tool_map = json.load(f)
        print(f"✅ Loaded bridge dictionary from {BRIDGE_DICT_PATH}")
    else:
        print(f"⚠️ Warning: Bridge dictionary not found at {BRIDGE_DICT_PATH}. IDs may be incomplete.")

    # 2. Load Model and Metadata
    model_manager = ModelManager(MODEL_PATH)
    model_manager.load()

    model = model_manager.get_model()
    reverse_dict, forward_dict, class_weights = model_manager.get_metadata()

    # 3. Predict Sequence
    print(f"AI is dreaming up a workflow starting from '{SEED_TOOL}'...")
    predicted_chain = generate_tool_sequence(model, forward_dict, reverse_dict, SEED_TOOL, max_len=MAX_STEPS)

    # --- NEW: VALIDATION LAYER ---
    GALAXY_URL = os.getenv("GALAXY_URL", "http://localhost:8080")
    API_KEY = os.getenv("GALAXY_API_KEY")

    validator = GalaxyValidator(GALAXY_URL, API_KEY)
    final_chain = validator.validate_and_fix_chain(predicted_chain, tool_map)

    for name in final_chain:
        tool_map[name] = validator.installed_tools[name]['full_id']

    print("\n✅ Validated Sequence (Exists on Instance):")
    print(" -> ".join(final_chain))

    print("\n✅ AI Predicted Sequence:")
    print(" -> ".join(predicted_chain))

    # 4. Assemble .ga (Pass only installed tools!)
    print("Assembling .ga file using installed tools only...")
    workflow_json = create_galaxy_workflow(
        final_chain,
        tool_mapping=tool_map,
        workflow_name="AI_Validated_Workflow"
    )

    output_filename = "ai_generated_workflow.ga"
    with open(output_filename, "w") as f:
        json.dump(workflow_json, f, indent=4)

    print(f"\n✨ Done! File saved as: {output_filename}")
    print("Action: Import this file into your Galaxy 'Workflows' menu.")

if __name__ == "__main__":
    main()