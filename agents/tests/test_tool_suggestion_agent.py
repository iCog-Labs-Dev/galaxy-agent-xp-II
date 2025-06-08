import json
import numpy as np
from ..suggesting_agent import ToolSuggestionAgent

def run_agent_tests(agent, test_file_path):
    with open(test_file_path, "r") as f:
        test_cases = json.load(f)

    for case in test_cases:
        prompt = case["prompt"]
        expected_tool = case["expected_tool"]

        suggestions = agent.suggest_tools(prompt, top_k=1)
        predicted_tool = suggestions[0]["name"]

        if predicted_tool == expected_tool:
            print(f"✅ PASS | Query: '{prompt}' → Predicted: {predicted_tool}")
        else:
            print(f"❌ FAIL | Query: '{prompt}' → Predicted: {predicted_tool}, Expected: {expected_tool}")

if __name__ == "__main__":
    agent = ToolSuggestionAgent(
        embeddings_path="agents/embeddings/galaxy_embeddings.npy",
        metadata_path="agents/embeddings/galaxy_metadata.json"
    )

    run_agent_tests(agent, "agents/tests/data/test_data.json")
