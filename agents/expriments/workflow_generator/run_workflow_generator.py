import os
import sys
import json
import numpy as np
import tensorflow as tf


# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)             
scripts_path = os.path.join(project_root, "scripts")     

if project_root not in sys.path:
    sys.path.append(project_root)
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

# --- IMPORTS ---
from scripts.train_transformer import create_model
from generator import generate_tool_sequence
from generate_ga_file import create_galaxy_workflow
from validator import GalaxyValidator

# --- CONFIGURATION ---
MODEL_WEIGHTS_PATH = os.path.join(project_root, "log/saved_model/200/tf_model_h5/model.h5")
F_DICT_PATH = os.path.join(project_root, "log/data/f_dict.txt")
R_DICT_PATH = os.path.join(project_root, "log/data/rev_dict.txt")
# The dictionary we created from workflow-connections.csv
BRIDGE_DICT_PATH = os.path.join(project_root, "log/data/tool_id_dict.txt")

CONFIG = {
    "embedding_dim": 128,
    "feed_forward_dim": 128,
    "maximum_path_length": 25,
    "dropout": 0.1,
    "n_heads": 4 
}
SEED_TOOL = "Grep1"
MAX_STEPS = 9 # Matches your predicted chain length

def load_dictionaries(f_path, r_path):
    with open(f_path, 'r') as f:
        f_dict = json.load(f)
    with open(r_path, 'r') as f:
        r_dict = {int(k): v for k, v in json.load(f).items()}
    return f_dict, r_dict

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

    # 2. Load AI Data
    f_dict, r_dict = load_dictionaries(F_DICT_PATH, R_DICT_PATH)
    vocab_size = len(f_dict) + 1

    # 3. Reconstruct Model
    print("Building Transformer architecture...")
    model = create_model(vocab_size, CONFIG)

    # 4. Load Weights
    if os.path.exists(MODEL_WEIGHTS_PATH):
        print(f"Loading weights from: {MODEL_WEIGHTS_PATH}")
        model.load_weights(MODEL_WEIGHTS_PATH)
    else:
        print(f"❌ Error: Weights file not found at {MODEL_WEIGHTS_PATH}")
        return

    # 5. Predict Sequence
    print(f"AI is dreaming up a workflow starting from '{SEED_TOOL}'...")
    predicted_chain = generate_tool_sequence(model, f_dict, r_dict, SEED_TOOL, max_len=MAX_STEPS)
    
    # --- NEW: VALIDATION LAYER ---
    GALAXY_URL = os.getenv("GALAXY_URL", "http://localhost:8080")
    API_KEY = os.getenv("GALAXY_API_KEY")

    validator = GalaxyValidator(GALAXY_URL, API_KEY)
    # This confirms the tool exists AND updates our mapping to match the exact version on your server
    final_chain = validator.validate_and_fix_chain(predicted_chain, tool_map)

    # Update the tool_map with the exact IDs found on the live server
    for name in final_chain:
        tool_map[name] = validator.installed_tools[name]['full_id']

    print("\n✅ Validated Sequence (Exists on Instance):")
    print(" -> ".join(final_chain))

    print("\n✅ AI Predicted Sequence:")
    print(" -> ".join(predicted_chain))
    
    # 6. Assemble .ga (Pass the tool_map here!)
    print("Assembling .ga file using connection-based mapping...")
    workflow_json = create_galaxy_workflow(
        predicted_chain, 
        tool_mapping=tool_map, # This tells the builder to use your unique tools
        workflow_name="AI_Validated_Workflow"
    )
    
    output_filename = "ai_generated_workflow.ga"
    with open(output_filename, "w") as f:
        json.dump(workflow_json, f, indent=4)

    print(f"\n✨ Done! File saved as: {output_filename}")
    print("Action: Import this file into your Galaxy 'Workflows' menu.")

if __name__ == "__main__":
    main()