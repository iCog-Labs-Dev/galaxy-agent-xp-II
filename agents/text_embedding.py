import json
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# Load data
with open("agents/data/galaxy_tools_may_3_2025_v1.json", "r", encoding="utf-8") as f: 
    data = json.load(f)

# Structure text data
texts = [
    f"{entry['name']} - {entry['description']} - {entry['category']} - {entry['help']}"
    for entry in data
]

# Load model
model = SentenceTransformer('intfloat/e5-base-v2')

# Encode texts
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

# Save embeddings
os.makedirs("agents/embeddings", exist_ok=True)
np.save("agents/embeddings/galaxy_embeddings.npy", embeddings)

with open("agents/embeddings/galaxy_metadata.json", "w", encoding="utf-8") as f:
    json.dump(data, f)

print(f"Encoded {len(embeddings)} texts and saved to agents/embeddings/")
