import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import os
import yaml

class ToolSuggestionAgent:
    """    A class to suggest tools based on user queries using a pre-trained SentenceTransformer model.
    This class loads a model and embeddings from specified paths, encodes user queries, computes cosine
    similarities with the embeddings, and returns a list of suggested tools based on the highest similarity scores
    and a score threshold.
    """
    config_file = "config.yml"
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file {config_file} not found. Please ensure it exists.")
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    # model_path = config["agent"]["base_model"]
    model_path = config["agent"]["finetuned_model"]
    embeddings_path = config["agent"]["tools_embeddings_path"]
    metadata_path = config["agent"]["tools_metadata_path"]   

    def __init__(self, model_path=model_path, embeddings_path=embeddings_path, metadata_path=metadata_path):
        # If not provided, use default paths
        self.model_path = model_path
        self.embeddings_path = embeddings_path
        self.metadata_path = metadata_path
        
        # Load the model and data
        print(f"🔄 Loading model from {model_path}")
        self.model = SentenceTransformer(model_path)
        self.embeddings = np.load(self.embeddings_path)

        # Load metadata
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def validate_tool_info(self, tool_info: dict) -> dict:
        """
        Ensure that all required fields exist and are non-null.
        Fills missing or null fields with defaults.
        """
        validated = {
            "id": tool_info.get("id") or "",
            "name": tool_info.get("name") or "",
            "description": tool_info.get("description") or "",
            "categories": tool_info.get("categories") or [],
            "version": tool_info.get("version") or "",
            "help": tool_info.get("help") or "",
        }
        # For convenience in output, take first category if exists, else 'Uncategorized'
        validated["category"] = validated["categories"][0] if validated["categories"] else "Uncategorized"
        return validated    
    
    def suggest_tools(self, query, top_k=5, score_threshold=0.05):
        # Encode query
        query_embedding = self.model.encode(query, convert_to_numpy=True)

        # Compute cosine similarities
        similarities = util.cos_sim(query_embedding, self.embeddings)[0]

        # Get top-k results
        top_results = np.argsort(-similarities)[:top_k]

        suggestions = []
        seen_tools = {}  # track highest score per tool

        for idx in top_results:
            raw_tool = self.metadata[idx]
            tool = self.validate_tool_info(raw_tool)  # validate against schema

            score = float(similarities[idx])

            # Only add if not already seen with close score
            if tool["name"] not in seen_tools or abs(seen_tools[tool["name"]] - score) > score_threshold:
                tool["score"] = score
                suggestions.append(tool)
                seen_tools[tool["name"]] = score

        return suggestions


if __name__ == "__main__":
    agent = ToolSuggestionAgent()
    user_query = input("Describe what you want to do: ")
    results = agent.suggest_tools(user_query, top_k=5)

    print("\nTop Suggestions:")
    for i, tool in enumerate(results, 1):
        print(f"\n{i}. {tool['name']} (ID: {tool['id']}, Score: {tool['score']:.4f})")
        print(f"   Description: {tool['description']}")
        print(f"   Help: {tool['help']}")
        print(f"   Category: {tool['category']}")
        print(f"   Version: {tool['version']}")