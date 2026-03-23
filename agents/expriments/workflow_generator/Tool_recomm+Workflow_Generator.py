# Integration of tool recommendation and workflow generation (Transformer+LLM mode)
import os
import sys
import json
import subprocess
import argparse
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.suggesting_agent import ToolSuggestionAgent
from agents.expriments.Next_Tool_Recommendation.model import ModelManager
from agents.expriments.workflow_generator.utils import extract_short_name_from_id

# Load tool_id_dict using project_root for clarity
tool_id_dict_path = os.path.join(project_root, 'agents', 'data', 'tool_id_dict.txt')
with open(tool_id_dict_path, 'r') as f:
    tool_id_dict = json.load(f)

def main_loop(top_k=5):
    agent = ToolSuggestionAgent()
    print("\n[INFO] Galaxy Workflow Generator Interactive Mode")
    print("Type your query and press Enter. Type 'exit' to quit.\n")
    while True:
        query = input("Enter your workflow query (or 'exit' to quit): ").strip()
        if query.lower() in ("exit", "quit"): 
            print("Exiting interactive mode.")
            break
        if not query:
            continue
        suggestions = agent.suggest_tools(query, top_k)
        if not suggestions:
            print("No tools found for query.")
            continue
        seed_short_name = None
        for tool in suggestions:
            short_name = extract_short_name_from_id(tool['id'])
            print(f"[DEBUG] Checking suggested tool: {tool['name']} (id: {tool['id']}) -> short name: {short_name}")
            if short_name in tool_id_dict:
                seed_short_name = short_name
                print(f"[INFO] Using seed tool: {seed_short_name}")
                break
            else:
                print(f"[INFO] Tool '{short_name}' not found in tool_id_dict. Trying next...")
        if not seed_short_name:
            print("[ERROR] No recommended tool found in tool_id_dict. Aborting workflow generation.")
            continue
        script_path = os.path.join(os.path.dirname(__file__), 'run_workflow_generator.py')
        command = [
            'python', script_path,
            '--mode', 'hybrid',
            '--seed_tool', seed_short_name,
            '--max_steps', '10',
            '--top_k', '5',
            '--top_p', '0.9',
            '--temperature', '1.0',
            '--repetition_penalty', '1.1',
            '--llm_provider', 'gemini',
            '--llm_model', 'gemini-2.5-flash',
            '--workflow_name', 'AI_Validated_Workflow',
            '--output_file', 'ai_generated_workflow.ga'
        ]
        print(f"[DEBUG] Subprocess command: {' '.join(command)}")
        print(f"\nCalling workflow generator with seed tool: {seed_short_name}")
        result = subprocess.run(command, capture_output=True, text=True)
        print("\nWorkflow Generator Output:")
        print(result.stdout)
        if result.stderr:
            print("\nWorkflow Generator Errors:")
            print(result.stderr)


if __name__ == "__main__":
    main_loop()
