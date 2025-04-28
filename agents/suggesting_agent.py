import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

class ToolSuggestionAgent:
    def __init__(self, model_path='intfloat/e5-base-v2', embedding_path='agents/embeddings/galaxy_embeddings.npy',
                 metadata_path='agents/embeddings/galaxy_metadata.json'):
        # Load model
        self.model = SentenceTransformer(model_path)
        # Load precomputed embeddings
        self.embeddings = np.load(embedding_path)
        # Load tool metadata
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
    
    def suggest_tools(self, query, top_k=5):
        # Encode the query
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Compute cosine similarities
        similarities = util.cos_sim(query_embedding, self.embeddings)[0]

        # Get top-k results
        top_results = np.argsort(-similarities)[:top_k]

        # Build suggestion list
        suggestions = []
        for idx in top_results:
            tool_info = self.metadata[idx]
            suggestions.append({
                "name": tool_info["name"],
                "description": tool_info["description"],
                "help": tool_info["help"],
                "category": tool_info["category"],
                "score": float(similarities[idx])
            })

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
