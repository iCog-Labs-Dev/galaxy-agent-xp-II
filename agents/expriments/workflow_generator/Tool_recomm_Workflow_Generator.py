# Integration of tool recommendation and workflow generation (Transformer+LLM mode)
import os
import sys
import json
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.suggesting_agent import ToolSuggestionAgent
from agents.expriments.workflow_generator.utils import extract_short_name_from_id

# Load tool_id_dict once when module is imported
tool_id_dict_path = os.path.join(project_root, 'agents', 'data', 'tool_id_dict.txt')
with open(tool_id_dict_path, 'r') as f:
    tool_id_dict = json.load(f)

# Default query and workflow parameters
DEFAULT_QUERY = "tool suite to create a consensus sequence from nanopore data"
TOP_K = 5  
DEFAULT_MAX_STEPS = 10 


def generate_workflow_for_query(query=None, max_steps=None, output_file='ai_generated_workflow.ga'):
    """
    Generate a workflow using a recommended seed tool based on a user query.

    Args:
        query (str, optional): User query describing desired workflow. Defaults to DEFAULT_QUERY.
        max_steps (int, optional): Number of steps in the generated workflow. Defaults to DEFAULT_MAX_STEPS.
        output_file (str): Name of the output workflow file.

    Returns:
        bool: True if workflow generation succeeded, False otherwise.
    """
    if query is None:
        query = DEFAULT_QUERY

    if max_steps is None:
        max_steps = DEFAULT_MAX_STEPS

    agent = ToolSuggestionAgent()

    suggestions = agent.suggest_tools(query, TOP_K)
    if not suggestions:
        print("[ERROR] No tools found for query.")
        return False

    seed_short_name = None
    for tool in suggestions:
        short_name = extract_short_name_from_id(tool['id'])
        if short_name in tool_id_dict:
            seed_short_name = short_name
            break

    if not seed_short_name:
        print("[ERROR] No recommended tool found in tool_id_dict. Aborting workflow generation.")
        return False

    # Call workflow generator subprocess
    script_path = os.path.join(os.path.dirname(__file__), 'run_workflow_generator.py')
    command = [
        'python', script_path,
        '--mode', 'hybrid',
        '--seed_tool', seed_short_name,
        '--max_steps', str(max_steps),
        '--top_k', str(TOP_K),
        '--top_p', '0.9',
        '--temperature', '1.0',
        '--repetition_penalty', '1.1',
        '--llm_provider', 'gemini',
        '--llm_model', 'gemini-2.5-flash',
        '--workflow_name', 'AI_Validated_Workflow',
        '--output_file', output_file
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("[ERROR] Workflow Generator encountered errors:")
        print(result.stderr)
        return False

    return True


if __name__ == "__main__":
    success = generate_workflow_for_query()
    if success:
        print("[INFO] Workflow generation completed successfully.")
    else:
        print("[INFO] Workflow generation failed.")