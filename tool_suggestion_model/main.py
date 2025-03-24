import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import dotenv
import os

# Load environment variables from .env file
dotenv.load_dotenv()

# Load the fine-tuned model
version = 2 # Change this to the version of the model you want to use
model_path = f'{os.getenv("MODEL_PATH")}{version}' # Path to the model this need to be set in enviroment variable
model = SentenceTransformer(model_path)

with open(os.getenv("DATA_PATH"), "r", encoding="utf-8") as file:
    data = json.load(file)

tools_data = [(entry["name"], entry["help"]) for entry in data]
tools_descriptions = [f"{name} - {help_text}" for name, help_text in tools_data]

tool_embeddings = model.encode(tools_descriptions)

new_task_description = "I’d like to run the 'Generic Variation Analysis on WGS PE Data, which workflow should I use?"
new_task_embedding = model.encode([new_task_description])

similarities = cosine_similarity(new_task_embedding, tool_embeddings)

top_3_indices = np.argsort(similarities[0])[::-1][:3]

top_3_tools = [(tools_data[i][0], similarities[0][i]) for i in top_3_indices]

for rank, (tool_name, score) in enumerate(top_3_tools, 1):
    print(f"Rank {rank}: {tool_name} (Similarity Score: {score:.4f})")