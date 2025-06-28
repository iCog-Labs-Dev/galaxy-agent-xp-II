import json
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# Load workflow metadata
with open("Agents/data/iwc_workflows_summary_june20_2025.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Structure texts for embedding
texts = [
    f"{entry['workflow_repository']} - {entry['category']} - {entry.get('readme_content', '')} - Tools: {', '.join(entry.get('tools_used', []))}"
    for entry in data
]

# Load model
model = SentenceTransformer('intfloat/e5-base-v2')

# Encode texts
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

# Save embeddings
os.makedirs("agents/embeddings", exist_ok=True)
np.save("agents/embeddings/iwc_workflow_embeddings.npy", embeddings)

# Save metadata alongside embeddings
with open("agents/embeddings/iwc_workflow_metadata.json", "w", encoding="utf-8") as f:
    json.dump(data, f)

print(f"Encoded {len(embeddings)} workflows and saved to agents/embeddings/")
