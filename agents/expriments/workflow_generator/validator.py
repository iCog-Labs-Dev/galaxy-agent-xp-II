from bioblend.galaxy import GalaxyInstance
import os
import json
import time

class GalaxyValidator:
    def __init__(self, url, api_key, timeout=15, skip_validation=False, cache_file="", cache_ttl=1800):
        self.gi = GalaxyInstance(url=url, key=api_key)
        self.installed_tools = {}
        self.tool_schemas = {}
        self.validation_ready = False
        self.tool_id_availability = {}
        self.skip_validation = skip_validation
        self.timeout = timeout
        self.cache_file = cache_file
        self.cache_ttl = cache_ttl
        self.schema_cache_file = ""
        if self.cache_file:
            root, ext = os.path.splitext(self.cache_file)
            self.schema_cache_file = f"{root}_schemas{ext or '.json'}"
        self._refresh_tool_cache()

    def _load_cache(self):
        if not self.cache_file:
            return False
        if not os.path.exists(self.cache_file):
            return False
        try:
            mtime = os.path.getmtime(self.cache_file)
            if (time.time() - mtime) > self.cache_ttl:
                return False
            with open(self.cache_file, "r") as handle:
                payload = json.load(handle)
            tools = payload.get("installed_tools", {})
            if not isinstance(tools, dict) or len(tools) == 0:
                return False
            self.installed_tools = tools
            self.validation_ready = True
            print(f"⚡ Loaded installed tools cache: {self.cache_file}")
            return True
        except Exception:
            return False

    def _save_cache(self):
        if not self.cache_file:
            return
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.cache_file, "w") as handle:
                json.dump({"installed_tools": self.installed_tools}, handle, indent=2)
        except Exception:
            pass

    def _load_schema_cache(self):
        if not self.schema_cache_file:
            return False
        if not os.path.exists(self.schema_cache_file):
            return False
        try:
            mtime = os.path.getmtime(self.schema_cache_file)
            if (time.time() - mtime) > self.cache_ttl:
                return False
            with open(self.schema_cache_file, "r") as handle:
                payload = json.load(handle)
            schemas = payload.get("tool_schemas", {})
            if not isinstance(schemas, dict):
                return False
            self.tool_schemas = schemas
            print(f"⚡ Loaded tool schema cache: {self.schema_cache_file}")
            return True
        except Exception:
            return False

    def _save_schema_cache(self):
        if not self.schema_cache_file:
            return
        try:
            cache_dir = os.path.dirname(self.schema_cache_file)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.schema_cache_file, "w") as handle:
                json.dump({"tool_schemas": self.tool_schemas}, handle, indent=2)
        except Exception:
            pass

    def _refresh_tool_cache(self):
        """Fetches all installed tools and stores them by their Short Name."""
        if self.skip_validation:
            print("⏭️ Skipping Galaxy validation by configuration.")
            self.validation_ready = False
            return

        if self._load_cache():
            self._load_schema_cache()
            return

        print("🔍 Connecting to Galaxy to verify installed tools...")
        try:
            # Bioblend supports requests timeout through this value.
            self.gi.timeout = self.timeout
            tools = self.gi.tools.get_tools()
            for t in tools:
                full_id = t['id']
                if "/" in full_id:
                    short_name = full_id.split("/")[-2]
                else:
                    short_name = full_id
                self.installed_tools[short_name] = {
                    "full_id": full_id,
                    "version": t.get('version', '1.0.0')
                }
            self.validation_ready = True
            self._save_cache()
            self._load_schema_cache()
        except Exception as exc:
            print(f"⚠️ Galaxy validation unavailable ({exc}). Continuing without instance validation.")
            self.validation_ready = False

    def _extract_schema_from_inputs(self, inputs, data_inputs, param_defaults):
        if isinstance(inputs, dict):
            iterable = list(inputs.values())
        elif isinstance(inputs, list):
            iterable = inputs
        else:
            iterable = []

        for inp in iterable:
            if not isinstance(inp, dict):
                continue
            inp_name = inp.get("name")
            inp_type = inp.get("type")

            if inp_type in ["section", "conditional", "repeat"]:
                nested = inp.get("inputs", [])
                self._extract_schema_from_inputs(nested, data_inputs, param_defaults)
                continue

            if inp_type in ["data", "data_collection"]:
                data_inputs.append(
                    {
                        "name": inp_name,
                        "optional": bool(inp.get("optional", False)),
                        "label": inp.get("label", inp_name),
                    }
                )
                continue

            if inp_name:
                default_val = inp.get("value")
                if default_val is None:
                    default_val = inp.get("default")
                if default_val is None and isinstance(inp.get("options"), list) and len(inp.get("options")) > 0:
                    first_opt = inp.get("options")[0]
                    if isinstance(first_opt, (list, tuple)) and len(first_opt) > 1:
                        default_val = first_opt[1]
                    else:
                        default_val = first_opt
                if default_val is not None:
                    param_defaults[inp_name] = default_val

    def get_tool_schema(self, short_name):
        if short_name in self.tool_schemas:
            return self.tool_schemas[short_name]

        if not self.validation_ready:
            return None

        tool_info = self.installed_tools.get(short_name)
        if not tool_info:
            return None

        full_id = tool_info.get("full_id")
        try:
            details = self.gi.tools.show_tool(full_id, io_details=True)
            data_inputs = []
            param_defaults = {}
            self._extract_schema_from_inputs(details.get("inputs", []), data_inputs, param_defaults)

            outputs = details.get("outputs", [])
            output_names = []
            if isinstance(outputs, list):
                for output in outputs:
                    if isinstance(output, dict):
                        name = output.get("name")
                        if name:
                            output_names.append(name)
            elif isinstance(outputs, dict):
                output_names = list(outputs.keys())

            schema = {
                "data_inputs": data_inputs,
                "param_defaults": param_defaults,
                "output_names": output_names,
                "raw_inputs": details.get("inputs", []),
            }
            self.tool_schemas[short_name] = schema
            self._save_schema_cache()
            return schema
        except Exception as exc:
            print(f"⚠️ Could not load schema for {short_name}: {exc}")
            return None

    def _get_default_value(self, inp):
        default_val = inp.get("value")
        if default_val is None:
            default_val = inp.get("default")
        if default_val is None and isinstance(inp.get("options"), list) and len(inp.get("options")) > 0:
            first_opt = inp.get("options")[0]
            if isinstance(first_opt, (list, tuple)) and len(first_opt) > 1:
                default_val = first_opt[1]
            else:
                default_val = first_opt
        return default_val

    def _enrich_from_inputs(self, inputs, payload, path_prefix=None):
        if path_prefix is None:
            path_prefix = []

        if isinstance(inputs, dict):
            iterable = list(inputs.values())
        elif isinstance(inputs, list):
            iterable = inputs
        else:
            iterable = []

        for inp in iterable:
            if not isinstance(inp, dict):
                continue

            inp_name = inp.get("name")
            inp_type = inp.get("type")
            optional = bool(inp.get("optional", False))
            if not inp_name:
                continue

            nested_key = "|".join(path_prefix + [inp_name]) if len(path_prefix) > 0 else inp_name

            if inp_type in ["section"]:
                self._enrich_from_inputs(inp.get("inputs", []), payload, path_prefix + [inp_name])
                continue

            if inp_type == "conditional":
                test_param = inp.get("test_param") or {}
                test_name = test_param.get("name")
                test_value = test_param.get("value")
                if test_value is None:
                    test_value = test_param.get("default")
                if test_name and test_value is not None and test_name not in payload:
                    payload[test_name] = test_value
                if test_name and test_value is not None:
                    payload.setdefault(nested_key + "|" + test_name, test_value)
                    cond_obj = payload.get(inp_name)
                    if not isinstance(cond_obj, dict):
                        cond_obj = {}
                    cond_obj.setdefault(test_name, test_value)
                    payload[inp_name] = cond_obj

                cases = inp.get("cases") or []
                selected_case = None
                if test_value is not None:
                    for case in cases:
                        if str(case.get("value")) == str(test_value):
                            selected_case = case
                            break
                if selected_case is None and len(cases) > 0:
                    selected_case = cases[0]

                if selected_case is not None:
                    self._enrich_from_inputs(selected_case.get("inputs", []), payload, path_prefix + [inp_name])
                continue

            if inp_type == "repeat":
                self._enrich_from_inputs(inp.get("inputs", []), payload, path_prefix + [inp_name])
                continue

            if inp_type in ["data", "data_collection"]:
                continue

            if inp_type == "data_column":
                if not optional:
                    payload.setdefault(inp_name, "c1")
                    payload.setdefault(nested_key, "c1")
                continue

            default_val = self._get_default_value(inp)
            if default_val is not None:
                payload.setdefault(inp_name, default_val)
                payload.setdefault(nested_key, default_val)

    def enrich_step_with_show_tool(self, short_name, input_connections, tool_state_payload):
        schema = self.get_tool_schema(short_name)
        if not schema:
            return tool_state_payload, input_connections

        data_inputs = schema.get("data_inputs", [])
        for data_in in data_inputs:
            name = data_in.get("name")
            if not name:
                continue
            if name not in input_connections and not bool(data_in.get("optional", False)):
                input_connections[name] = {"id": 0, "output_name": "output"}
            if name not in tool_state_payload:
                tool_state_payload[name] = {"__class__": "RuntimeValue"}

        raw_inputs = schema.get("raw_inputs", [])
        self._enrich_from_inputs(raw_inputs, tool_state_payload, path_prefix=[])
        return tool_state_payload, input_connections

    def validate_and_fix_chain(self, predicted_chain, tool_mapping):
        """
        Checks each tool in the chain. If not on instance, 
        it tries to find a local alternative or skips it.
        """
        if not self.validation_ready:
            return predicted_chain

        validated_chain = []
        for tool_name in predicted_chain:
            if tool_name in self.installed_tools:
                validated_chain.append(tool_name)
            else:
                print(f"⚠️ Tool '{tool_name}' not found on this Galaxy instance. Skipping...")
                # Optional: Add logic here to find a fuzzy match 
                # (e.g., if 'bwa' is missing, look for 'bwa_mem')
        
        return validated_chain

    def is_tool_id_available(self, full_id):
        if not self.validation_ready:
            return True
        if full_id in self.tool_id_availability:
            return self.tool_id_availability[full_id]
        try:
            self.gi.tools.show_tool(full_id, io_details=False)
            self.tool_id_availability[full_id] = True
            return True
        except Exception:
            self.tool_id_availability[full_id] = False
            return False