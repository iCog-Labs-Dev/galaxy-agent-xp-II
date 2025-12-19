class NodeBuilder:
    def _generate_id(self, *args):
        import hashlib
        s = "_".join([str(a) for a in args if a is not None])
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    # -----------------------
    # Workflow Node
    # -----------------------
    def create_workflow(self, data):
        workflow_id = self._generate_id(data["workflow_repository"], data.get("file_name"))
        return {
            "label": "Workflow",
            "properties": {
                "workflow_id": workflow_id,
                "name": data["workflow_repository"],
                "category": data["category"],
                "file_name": data.get("file_name"),
                "download_url": data.get("raw_download_url"),
                "number_of_steps": data.get("number_of_steps"),
                "readme": data.get("readme", ""),
                "has_readme": data.get("has_readme", False),
                "has_changelog": data.get("has_changelog", False),
                "has_test_data": data.get("has_test_data", False),
                "planemo_tests": data.get("planemo_tests", [])
            }
        }

    # -----------------------
    # Step Node
    # -----------------------
    def create_step(self, step, workflow_id):
        step_uid = self._generate_id(workflow_id, step.get("step_id"))
        tool_repo = step.get("tool_shed_repository", {})

        # Correct Step Name Logic
        if step.get("tool_id"):
            step_name = step["tool_id"]          # always use the real tool ID
        elif step.get("name"):
            step_name = step["name"]
        else:
            step_name = f"Step_{step.get('step_id', step_uid)}"

        return {
            "label": "Step",
            "properties": {
                "step_uid": step_uid,
                "workflow_id": workflow_id,
                "step_id": step.get("step_id"),
                "name": step_name,
                "type": step.get("type"),
                "annotation": step.get("annotation"),
                "tool_id": step.get("tool_id"),
                "tool_version": step.get("tool_version"),
                "input_connections": __import__("json").dumps(step.get("input_connections", {})),
                "tool_owner": tool_repo.get("owner"),
                "tool_repo": tool_repo.get("name"),
                "tool_shed_url": tool_repo.get("tool_shed"),
        }
    }

    # -----------------------
    # Tool Node
    # -----------------------
    def create_tool(self, tool_id, version=None, repo_name=None, owner=None):
        """
        Create a Tool node to be used by USES_TOOL edges
        """
        node_id = self._generate_id(tool_id, version)
        return {
            "label": "Tool",
            "properties": {
                "tool_id": tool_id,
                "tool_uid": node_id,
                "version": version,
                "repo_name": repo_name,
                "owner": owner
            }
        }

    # -----------------------
    # Input / Output Nodes
    # -----------------------
    def create_input_node(self, workflow_id, step_id, name, description):
        input_uid = self._generate_id(workflow_id, step_id, name, description)
        return {
            "label": "Input",
            "properties": {
                "input_uid": input_uid,
                "workflow_id": workflow_id,
                "step_id": step_id,
                "name": name,
                "description": description
            }
        }

    def create_output_node(self, workflow_id, step_id, name, description):
        output_uid = self._generate_id(workflow_id, step_id, name, description)
        return {
            "label": "Output",
            "properties": {
                "output_uid": output_uid,
                "workflow_id": workflow_id,
                "step_id": step_id,
                "name": name,
                "description": description
            }
        }

    # -----------------------
    # Category Node
    # -----------------------
    def create_category(self, name):
        category_id = self._generate_id(name)
        return {
            "label": "Category",
            "properties": {
                "name": name,
                "category_id": category_id
            }
        }
