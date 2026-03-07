import json
import os

def create_galaxy_workflow(predicted_tool_names, tool_mapping=None, workflow_name="AI_Validated_Workflow"):
    """
    Assembles the .ga file using the bridge dictionary for ID resolution.
    Fixed: Added internal 'id' fields to prevent Galaxy KeyError.
    """
    
    # 1. Resolve the Dictionary
    if tool_mapping is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dict_path = os.path.join(project_root, "agents", "data", "tool_id_dict.txt")
        
        if os.path.exists(dict_path):
            with open(dict_path, 'r') as f:
                tool_mapping = json.load(f)
            print(f"✅ Bridge Dictionary Loaded: {len(tool_mapping)} tools available.")
        else:
            tool_mapping = {}
            print(f"⚠️ Warning: Could not find dictionary at {dict_path}")

    workflow = {
        "a_galaxy_workflow": "true",
        "format-version": "0.1",
        "name": workflow_name,
        "steps": {},
        "annotation": "AI-Generated via Transformer Model using Workflow-Connections Mapping"
    }

    # Step 0: Input Dataset (Must have "id": 0)
    workflow["steps"]["0"] = {
        "id": 0,
        "type": "data_input",
        "label": "Primary Input",
        "position": {"left": 0, "top": 300},
        "outputs": [{"name": "output", "type": "data"}],
        "workflow_outputs": []
    }

    extra_input_counter = 100 

    for i, short_name in enumerate(predicted_tool_names):
        step_id_int = i + 1
        step_id_str = str(step_id_int)
        prev_step_id = i
        
        # --- SMART ID RESOLUTION ---
        full_id = tool_mapping.get(short_name)
        
        if not full_id:
            search_name = short_name.lower().split('_')[0]
            for key, val in tool_mapping.items():
                if search_name in key.lower():
                    full_id = val
                    break
        
        if not full_id:
            full_id = short_name
            annotation = f"⚠️ Note: {short_name} not found in historical connection data."
        else:
            annotation = ""

        # --- WIRING LOGIC ---
        is_multi = any(kw in short_name.lower() for kw in ["join", "merge", "compare"])
        
        if is_multi:
            side_id_int = extra_input_counter
            side_id_str = str(side_id_int)
            
            # Create side input step with its own internal ID
            workflow["steps"][side_id_str] = {
                "id": side_id_int,
                "type": "data_input",
                "label": f"Side-input for {short_name}",
                "position": {"left": step_id_int * 300, "top": 550},
                "outputs": [{"name": "output", "type": "data"}],
                "workflow_outputs": []
            }
            
            input_conns = {
                "input1": {"id": prev_step_id, "output_name": "output"},
                "input2": {"id": side_id_int, "output_name": "output"}
            }
            extra_input_counter += 1
        else:
            port = "bam" if "bam" in short_name.lower() else "input"
            input_conns = {port: {"id": prev_step_id, "output_name": "output"}}

        # Create tool step with its own internal ID
        workflow["steps"][step_id_str] = {
            "id": step_id_int,
            "tool_id": full_id,
            "label": f"Step {step_id_str}: {short_name}",
            "type": "tool",
            "annotation": annotation,
            "position": {"left": step_id_int * 300, "top": 300},
            "input_connections": input_conns,
            "tool_state": json.dumps({"__page__": 0}),
            "workflow_outputs": [{"output_name": "output", "label": f"out_{short_name}"}] if i == len(predicted_tool_names)-1 else []
        }

    return workflow