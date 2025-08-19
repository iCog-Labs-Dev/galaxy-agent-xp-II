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
        self.model = SentenceTransformer(model_path)
        self.embeddings = np.load(self.embeddings_path)
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
    
    
    def suggest_tools(self, query, top_k=5, score_threshold=0.05):
        # Encode the query
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Compute cosine similarities
        similarities = util.cos_sim(query_embedding, self.embeddings)[0]

        # Get top-k results
        top_results = np.argsort(-similarities)[:top_k]

        # Build suggestion list
        suggestions = []
        seen_tools = {}  # Dictionary to store tool names and their highest similarity score

        for idx in top_results:
            tool_info = self.metadata[idx]
            tool_name = tool_info["name"]
            score = float(similarities[idx])

            # If the tool is not in the seen_tools dictionary or the score difference is large enough, add it
            if tool_name not in seen_tools or abs(seen_tools[tool_name] - score) > score_threshold:
                suggestions.append({
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "help": tool_info["help"],
                    "category": tool_info.get("category", "Uncategorized") or "Uncategorized",
                    "score": float(similarities[idx])
                })

                # Update the seen_tools dictionary with the highest score for this tool
                seen_tools[tool_name] = score

        return suggestions

if __name__ == "__main__":
    agent = ToolSuggestionAgent()
    user_query = input("Describe what you want to do: ")
    results = agent.suggest_tools(user_query, top_k=5)

    print("\nTop Suggestions:")
    for i, tool in enumerate(results, 1):
        print(f"\n{i}. {tool['name']} (Score: {tool['score']:.4f})")
        print(f"   Description: {tool['description']}")
        print(f"   Help: {tool['help']}")
        print(f"   Category: {tool['category']}")
