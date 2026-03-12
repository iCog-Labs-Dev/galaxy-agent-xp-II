import json
import os

def _resolve_tool_id(short_name, tool_mapping):
    full_id = tool_mapping.get(short_name)
    if full_id:
        return full_id, ""

    search_name = short_name.lower().split('_')[0]
    for key, val in tool_mapping.items():
        if search_name in key.lower():
            return val, ""

    return short_name, f"⚠️ Note: {short_name} not found in historical connection data."


def _runtime_value():
    return {"__class__": "RuntimeValue"}


def _apply_tool_templates(short_name, tool_state_payload):
    name = short_name.lower()

    if name == "tp_easyjoin_tool":
        tool_state_payload.setdefault("column1", "c1")
        tool_state_payload.setdefault("column2", "c1")

    if name == "join1":
        tool_state_payload.setdefault("field1", "c1")
        tool_state_payload.setdefault("field2", "c1")
        tool_state_payload.setdefault("fill_empty_columns", "no_fill")
        tool_state_payload.setdefault("fill_empty_columns_switch", "no_fill")
        tool_state_payload.setdefault("fill_empty_columns", {"fill_empty_columns_switch": "no_fill"})
        tool_state_payload.setdefault("fill_empty_columns|fill_empty_columns_switch", "no_fill")

    if name == "tp_sort_header_tool":
        tool_state_payload.setdefault("column", "c1")

    if name == "add_a_column1":
        tool_state_payload.setdefault("header_lines_select", "no")
        tool_state_payload.setdefault("header_lines_conditional", {"header_lines_select": "no"})
        tool_state_payload.setdefault("header_lines_conditional|header_lines_select", "no")

    if name == "tp_cut_tool":
        tool_state_payload.setdefault("cut_element", "-f")
        tool_state_payload.setdefault("list", "1")
        tool_state_payload.setdefault("fields", "1")
        tool_state_payload.setdefault("cut_type_options|list", "1")
        tool_state_payload.setdefault("cut_type_options|case0|list", "1")
        tool_state_payload.setdefault("cut_by", "-f")
        tool_state_payload.setdefault("delimiter", "T")
        tool_state_payload.setdefault("delimited_by", "T")
        tool_state_payload.setdefault("header", "N")
        tool_state_payload.setdefault("cut_type_options", {"cut_element": "-f", "list": "1"})
        tool_state_payload.setdefault("cut_type_options|cut_element", "-f")
        tool_state_payload.setdefault("cut_type_options|delimiter", "T")

    if name == "grouping1":
        tool_state_payload.setdefault("groupcol", "c1")
        tool_state_payload.setdefault("operations|opcol", "c1")

    if name == "datamash_ops":
        tool_state_payload.setdefault("grouping", "1")


def create_galaxy_workflow(predicted_tool_names, tool_mapping=None, workflow_name="AI_Validated_Workflow", validator=None):
    """
    Assembles the .ga file using the bridge dictionary for ID resolution.
    Fixed: Added internal 'id' fields to prevent Galaxy KeyError.
    """
    
    # 1. Resolve the Dictionary
    if tool_mapping is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dict_path = os.path.join(project_root, "data", "tool_id_dict.txt")
        
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
    produced_output_name = {0: "output"}

    for i, short_name in enumerate(predicted_tool_names):
        step_id_int = i + 1
        step_id_str = str(step_id_int)
        prev_step_id = i
        full_id, annotation = _resolve_tool_id(short_name, tool_mapping)
        if validator and getattr(validator, "validation_ready", False):
            inst_info = validator.installed_tools.get(short_name)
            if inst_info and isinstance(inst_info, dict) and inst_info.get("full_id"):
                full_id = inst_info.get("full_id")
                annotation = ""

        if validator and hasattr(validator, "is_tool_id_available"):
            if not validator.is_tool_id_available(full_id):
                print(f"⚠️ Skipping tool not available on instance: {short_name} ({full_id})")
                continue

        schema = validator.get_tool_schema(short_name) if validator else None
        data_inputs = schema.get("data_inputs", []) if schema else []
        param_defaults = schema.get("param_defaults", {}) if schema else {}
        output_names = schema.get("output_names", []) if schema else []

        if len(data_inputs) == 0:
            if any(kw in short_name.lower() for kw in ["join", "merge", "compare"]):
                data_inputs = [
                    {"name": "input1", "optional": False, "label": "input1"},
                    {"name": "input2", "optional": False, "label": "input2"},
                ]
            else:
                port = "bam" if "bam" in short_name.lower() else "input"
                data_inputs = [{"name": port, "optional": False, "label": port}]

        input_conns = {}
        for idx, data_in in enumerate(data_inputs):
            port_name = data_in.get("name") or f"input{idx+1}"
            is_optional = bool(data_in.get("optional", False))

            if idx == 0:
                prev_out = produced_output_name.get(prev_step_id, "output")
                input_conns[port_name] = {"id": prev_step_id, "output_name": prev_out}
            elif not is_optional:
                side_id_int = extra_input_counter
                side_id_str = str(side_id_int)
                workflow["steps"][side_id_str] = {
                    "id": side_id_int,
                    "type": "data_input",
                    "label": f"Side-input for {short_name}:{port_name}",
                    "position": {"left": step_id_int * 300, "top": 550 + (idx * 100)},
                    "outputs": [{"name": "output", "type": "data"}],
                    "workflow_outputs": []
                }
                input_conns[port_name] = {"id": side_id_int, "output_name": "output"}
                extra_input_counter += 1

        tool_state_payload = {"__page__": 0}
        for k, v in param_defaults.items():
            if k not in tool_state_payload:
                tool_state_payload[k] = v

        # Galaxy also expects runtime placeholders for connected data inputs.
        for data_in in data_inputs:
            port_name = data_in.get("name")
            if port_name and port_name not in tool_state_payload:
                tool_state_payload[port_name] = _runtime_value()

        _apply_tool_templates(short_name, tool_state_payload)

        # Final schema-aware verification/enrichment from Galaxy show_tool metadata.
        if validator and hasattr(validator, "enrich_step_with_show_tool"):
            tool_state_payload, input_conns = validator.enrich_step_with_show_tool(
                short_name,
                input_conns,
                tool_state_payload,
            )

        # Create tool step with its own internal ID
        workflow["steps"][step_id_str] = {
            "id": step_id_int,
            "tool_id": full_id,
            "label": f"Step {step_id_str}: {short_name}",
            "type": "tool",
            "annotation": annotation,
            "position": {"left": step_id_int * 300, "top": 300},
            "input_connections": input_conns,
            "tool_state": json.dumps(tool_state_payload),
            "workflow_outputs": [{"output_name": "output", "label": f"out_{short_name}"}] if i == len(predicted_tool_names)-1 else []
        }

        if output_names:
            workflow["steps"][step_id_str]["workflow_outputs"] = []
            if i == len(predicted_tool_names) - 1:
                out_name = output_names[0]
                workflow["steps"][step_id_str]["workflow_outputs"] = [{"output_name": out_name, "label": f"out_{short_name}"}]
            produced_output_name[step_id_int] = output_names[0]
        else:
            produced_output_name[step_id_int] = "output"

    return workflow