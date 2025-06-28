import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

class WorkflowSuggestionAgent:
    def __init__(self, model_path='intfloat/e5-base-v2', embeddings_path=None, metadata_path=None):
        # If not provided, use default paths
        self.embeddings_path = embeddings_path or 'agents/embeddings/iwc_workflow_embeddings.npy'
        self.metadata_path = metadata_path or 'agents/embeddings/iwc_workflow_metadata.json'
        
        # Load the model and data
        self.model = SentenceTransformer(model_path)
        self.embeddings = np.load(self.embeddings_path)
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
    
    
    def suggest_workflows(self, query, top_k=5, score_threshold=0.05):
        # Encode the query
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Compute cosine similarities
        similarities = util.cos_sim(query_embedding, self.embeddings)[0]

        # Get top-k results
        top_results = np.argsort(-similarities)[:top_k]

        # Build suggestion list
        suggestions = []
        seen_workflows = {}

        for idx in top_results:
            workflow_info = self.metadata[idx]
            workflow_name = workflow_info["workflow_repository"]
            score = float(similarities[idx])

            # If not seen yet or significantly different in score
            if workflow_name not in seen_workflows or abs(seen_workflows[workflow_name] - score) > score_threshold:
                suggestions.append({
                    "name": workflow_name,
                    "category": workflow_info.get("category", "Uncategorized") or "Uncategorized",
                    "tools_used": workflow_info.get("tools_used", []),
                    "has_readme": workflow_info.get("has_readme", False),
                    "readme_excerpt": workflow_info.get("readme_content", "")[:300],  # Preview first 300 chars
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
        print(f"   Has README: {'✅' if wf['has_readme'] else '❌'}")
        print(f"   Description: {wf['readme_excerpt']}...")
