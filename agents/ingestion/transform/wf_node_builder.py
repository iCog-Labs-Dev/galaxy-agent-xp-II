# transform/wf_node_builder.py
import hashlib
import json


class NodeBuilder:

    def _hash(self, *parts):
        value = "_".join(str(p) for p in parts if p)
        return hashlib.md5(value.encode("utf-8")).hexdigest()

    # -----------------------
    # Workflow
    # -----------------------
    def create_workflow(self, *, name, category, root,
                        file_name=None,
                        download_url=None,
                        number_of_steps=None,
                        readme="",
                        has_readme=False,
                        has_changelog=False,
                        has_test_data=False,
                        planemo_tests=None,
                        embedding=None):

        if root:
            workflow_id = self._hash(name)
        else:
            workflow_id = self._hash(name, file_name)

        return {
            "label": "Workflow",
            "properties": {
                "workflow_id": workflow_id,
                "name": name,
                "category": category,
                "file_name": file_name,
                "download_url": download_url,
                "number_of_steps": number_of_steps,
                "readme": readme,
                "has_readme": has_readme,
                "has_changelog": has_changelog,
                "has_test_data": has_test_data,
                "planemo_tests": planemo_tests or [],
                "embedding": embedding if root else None,
                "root": root
            }
        }

    # -----------------------
    # Step
    # -----------------------
    def create_step(self, step, workflow_id):
        step_uid = self._hash(workflow_id, step.get("step_id"))

        tool_repo = step.get("tool_shed_repository", {}) or {}

        return {
            "label": "Step",
            "properties": {
                "step_uid": step_uid,
                "workflow_id": workflow_id,
                "step_id": step.get("step_id"),
                "name": step.get("tool_id") or step.get("name"),
                "type": step.get("type"),
                "annotation": step.get("annotation"),
                "tool_id": step.get("tool_id"),
                "tool_version": step.get("tool_version"),
                "input_connections": json.dumps(step.get("input_connections", {})),
                "tool_owner": tool_repo.get("owner"),
                "tool_repo": tool_repo.get("name"),
                "tool_shed_url": tool_repo.get("tool_shed"),
            }
        }

    # -----------------------
    # Input / Output
    # -----------------------
    def create_input(self, workflow_id, step_id, name, description):
        uid = self._hash(workflow_id, step_id, name, description)
        return {
            "label": "Input",
            "properties": {
                "input_uid": uid,
                "workflow_id": workflow_id,
                "step_id": step_id,
                "name": name,
                "description": description
            }
        }

    def create_output(self, workflow_id, step_id, name, description):
        uid = self._hash(workflow_id, step_id, name, description)
        return {
            "label": "Output",
            "properties": {
                "output_uid": uid,
                "workflow_id": workflow_id,
                "step_id": step_id,
                "name": name,
                "description": description
            }
        }

    # -----------------------
    # Category
    # -----------------------
    def create_category(self, name):
        return {
            "label": "Category",
            "properties": {
                "category_id": self._hash(name),
                "name": name
            }
        }
