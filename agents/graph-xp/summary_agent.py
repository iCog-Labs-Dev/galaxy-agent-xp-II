import json
import numpy as np
import os
import yaml
from sentence_transformers import SentenceTransformer, util


class ToolSuggestionAgent:
    """
    Suggest tools based on a query using a pre-trained SentenceTransformer model.
    Loads embeddings and metadata lazily to avoid heavy operations on import.
    """

    # Default config paths
    config_file = "config.yml"
    _config_loaded = False

    @classmethod
    def load_config(cls):
        if cls._config_loaded:
            return
        if not os.path.exists(cls.config_file):
            raise FileNotFoundError(
                f"Configuration file {cls.config_file} not found. Please ensure it exists."
            )
        with open(cls.config_file, "r") as f:
            config = yaml.safe_load(f)
        cls.model_path = config["agent"]["finetuned_model"]
        cls.embeddings_path = config["agent"]["tools_embeddings_path"]
        cls.metadata_path = config["agent"]["tools_metadata_path"]
        cls._config_loaded = True

    def __init__(self, model_path=None, embeddings_path=None, metadata_path=None):
        self.load_config()

        # Use provided paths or fallback to config
        self.model_path = model_path or self.model_path
        self.embeddings_path = embeddings_path or self.embeddings_path
        self.metadata_path = metadata_path or self.metadata_path

        # Load model and embeddings lazily
        print(f"🔄 Loading model from {self.model_path}")
        self.model = SentenceTransformer(self.model_path)
        self.embeddings = np.load(self.embeddings_path)

        # Load metadata
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def validate_tool_info(self, tool_info: dict) -> dict:
        validated = {
            "id": tool_info.get("id") or "",
            "name": tool_info.get("name") or "",
            "description": tool_info.get("description") or "",
            "categories": tool_info.get("categories") or [],
            "version": tool_info.get("version") or "",
            "help": tool_info.get("help") or "",
        }
        validated["category"] = validated["categories"][0] if validated["categories"] else "Uncategorized"
        return validated

    def suggest_tools(self, query, top_k=5, score_threshold=0.05):
        query_embedding = self.model.encode(query, convert_to_numpy=True).astype(np.float32)
        similarities = util.pytorch_cos_sim(query_embedding, self.embeddings)[0]

        top_results = np.argsort(-similarities)[:top_k]
        suggestions = []
        seen_tools = {}

        for idx in top_results:
            raw_tool = self.metadata[idx]
            tool = self.validate_tool_info(raw_tool)
            score = float(similarities[idx])

            if tool["name"] not in seen_tools or abs(seen_tools[tool["name"]] - score) > score_threshold:
                tool["score"] = score
                suggestions.append(tool)
                seen_tools[tool["name"]] = score

        return suggestions


if __name__ == "__main__":
    agent = ToolSuggestionAgent()
    query = input("Describe what you want to do: ")
    results = agent.suggest_tools(query, top_k=5)

    print("\nTop Suggestions:")
    for i, tool in enumerate(results, 1):
        print(f"{i}. {tool['name']} (ID: {tool['id']}, Score: {tool['score']:.4f})")
        print(f"   Description: {tool['description']}")
        print(f"   Help: {tool['help']}")
        print(f"   Category: {tool['category']}")
        print(f"   Version: {tool['version']}")