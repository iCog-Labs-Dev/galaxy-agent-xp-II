# Galaxy Tools Fetcher using BioBlend

This Python script connects to a Galaxy instance using the [BioBlend](https://bioblend.readthedocs.io/en/latest/) library. It retrieves available tools and outputs their information in JSON format. The connection credentials (URL and API key) are securely managed using a `.env` file.

---

## Features

✅ Connect to a Galaxy instance  
✅ Retrieve and list available tools  
✅ Securely manage API credentials via environment variables  
✅ Extendable to use SBERT for further processing 

---

## Prerequisites

- Python 3.7+
- Access to a Galaxy instance with an API key

---

## Installation

1. **Clone this repository**  
   ```bash
   git clone https://github.com/iCog-Labs-Dev/galaxy-agent-xp-II.git
   cd galaxy-agent-xp-II
   ```
2. **Create and activate a virtual environment (optional but recommended)**
   ```
   python -m venv venv
   source venv/bin/activate    # On Windows, use venv\Scripts\activate
   ```
 3. **Install the required packages**
    ```
    pip install -r requirements.txt
    ```
4. **Create a .env file in the project root directory.**
   ```
   GALAXY_URL=https://usegalaxy.org
   GALAXY_API_KEY="your_api_key_here"

   ```
 5. **Usage**
    
    a. **fetch tools**
    ```
    python utilities/tools_metadata_downloader/run.py
    ```
    b. **fetch workflows **
    ```
    python utilities/workflow_downloader/run.py
    ```

    c. **copy the preprocessed tools and workflows to the agents/data/**
    
    
    d. **embed the preprocessed tools**
    ```
    python agents/scripts/embed_tools.py --input agents/data/preprocessed_tools_{time_stamp}.json
    ```
    e. **embed the preprocessed workflow**
    ```
    python agents/scripts/embed_workflows.py --input/data/preprocessed_workflows_{time_stamp}.json
    ```

    f. **copy the names of the embedded files to the config.yml**

    g. **use the agents for recommendation**
    ```
    python agents/suggesting_agent.py
    ```
    and ask about the tools 
    
# Galaxy Tools Suggestion Using intfloat/e5-large 
A FastAPI-powered AI agent for suggesting relevant Galaxy tools based on natural language queries using sentence embeddings and cosine similarity.

## Usage of the agent 
After cloning this repository go to agents
```
cd agents
```
## 📌 1️⃣ Configure Paths
Open configs/config.py and set the following paths:
```
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_to_encode_path: str = "data/tools_metadata.json"  # raw data (JSON format)
    embeddings_path: str = "embeddings/galaxy_embeddings.npy"
    metadata_path: str = "embeddings/galaxy_metadata.json"
```
## 📌 2️⃣ Encode Your Data
After setting your config, run the embedding script to encode your tools' metadata JSON into embeddings (.npy) and save metadata as a JSON file for lookup.
```
python agents/text_embedding.py

```
This will:

-  Load your raw JSON metadata
-  Generate sentence embeddings
-  Save embeddings to embeddings/galaxy_embeddings.npy
-  Save clean metadata to embeddings/galaxy_metadata.json

## 📌 3️⃣ Run the FastAPI Backend
Start your API server with:
```
uvicorn app:app --reload
```
## 📌 4️⃣ Test the API
🔍 Health Check
```
GET http://127.0.0.1:8000/health
```
Response
```
{"status": "ok"}
```
## 🎯 Tool Suggestion
```
POST http://127.0.0.1:8000/suggest
```
Request Body
```
{
  "query": "align sequences to a reference genome",
  "top_k": 5
}
```
Response

```
{
  "results": [
    {
      "name": "Tool A",
      "description": "Performs sequence alignment",
      "help": "long help section",
      "category": "Alignment",
      "score": 0.92
    }
  ]
}
```

