import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

class ToolSuggestionAgent:
    def __init__(self, model_path='intfloat/e5-base-v2', embeddings_path=None, metadata_path=None):
        # If not provided, use default paths
        self.embeddings_path = embeddings_path or 'embeddings/galaxy_embeddings.npy'
        self.metadata_path = metadata_path or 'embeddings/galaxy_metadata.json'
        
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
                    "name": tool_name,
                    "description": tool_info["description"],
                    "help": tool_info["help"],
                    "category": tool_info["category"],
                    "score": score
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
