import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import os
import yaml

class WorkflowSuggestionAgent:
    """
    A simple agent to suggest workflows based on user queries.
    It uses a pre-trained SentenceTransformer model to encode queries and workflows,
    and retrieves the most relevant workflows based on cosine similarity.
    """
    config_file = "config.yml"
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found. Please ensure it exists.")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    #model_path = config["agent"]["base_model"]
    model_path = config["agent"]["finetuned_model"]
    embeddings_path = config["agent"]["workflow_embeddings_path"]
    metadata_path = config["agent"]["workflow_metadata_path"]
    def __init__(self, model_path=model_path, embeddings_path=embeddings_path, metadata_path=metadata_path):
        # If not provided, use default paths
        self.model_path = model_path
        self.embeddings_path = embeddings_path
        self.metadata_path = metadata_path 
        
        # Load the model and data
        self.model = SentenceTransformer(model_path)
        self.embeddings = np.load(self.embeddings_path)
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
    def validate_workflow_metadata(self, workflow_info: dict) -> dict:
        """
        Ensure that all required fields exist and are non-null.
        Fills missing or null fields with defaults.
        """
        validated = {
            "workflow_repository": workflow_info.get("workflow_repository") or "",
            "category": workflow_info.get("category") or "",
            "tool_names": workflow_info.get("tool_names") or [],
            "readme_cleaned": workflow_info.get("readme_cleaned") or "",
            "raw_download_url": workflow_info.get("raw_download_url") or ""
        }
        return validated
    
    def suggest_workflows(self, query, top_k=5, score_threshold=0.05):
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        similarities = util.pytorch_cos_sim(query_embedding, self.embeddings)[0]

        top_results = np.argsort(-similarities)[:top_k]
    
        suggestions = []
        seen_workflows = {}
    
        for idx in top_results:
            workflow_info = self.metadata[idx]
            workflow_name = workflow_info["workflow_repository"]
            score = float(similarities[idx])
        
            # Skip if below threshold
            if score < score_threshold:
                continue
            
            # Internal validation
            self.validate_workflow_metadata(workflow_info)
        
            if workflow_name not in seen_workflows or abs(seen_workflows[workflow_name] - score) > score_threshold:
                suggestions.append({
                    "name": workflow_name,
                    "category": workflow_info.get("category", "Uncategorized") or "Uncategorized",
                    "tools_used": workflow_info.get("tool_names", []),
                    "readme_excerpt": workflow_info.get("readme_cleaned", ""),
                    "download_url": workflow_info.get("raw_download_url", ""),
                    "score": score
                })
                seen_workflows[workflow_name] = score

        return suggestions



if __name__ == "__main__":
    agent = WorkflowSuggestionAgent()
    user_query = input("Describe what you want to do: ")
    results = agent.suggest_workflows(user_query, top_k=5)

    print("\nTop Workflow Suggestions:")
    for i, wf in enumerate(results, 1):
        print(f"\n{i}. {wf['name']} (Score: {wf['score']:.4f})")
        print(f"   Category: {wf['category']}")
        print(f"   Tools Used: {', '.join(wf['tools_used']) if wf['tools_used'] else 'N/A'}")
        print(f"   Download URL: {wf['download_url'] if wf['download_url'] else 'No download available'}")
        print(f"   Readme: {wf['readme_excerpt'] if wf['readme_excerpt'] else 'No description available'}")
