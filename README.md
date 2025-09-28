# Galaxy Agent XP-II – AI-Powered Galaxy Tool & Workflow Recommender

Galaxy Agent XP-II is a **FastAPI-powered AI assistant** that recommends **Galaxy tools and workflows** based on natural language queries. It integrates **Galaxy's BioBlend API**, **GitHub-hosted workflows**, and **large language models (LLMs)** such as **Gemini** and **SBERT embeddings** to provide intelligent recommendations.

## Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
  - [Prerequisites](#1-prerequisites)
  - [Installation](#2-installation)
  - [Configuration](#3-configuration)
  - [Data Preparation & Embeddings](#4-data-preparation--embeddings)
- [API Endpoints](#-api-endpoints)
- [How It Works](#-how-it-works)
- [Example Usage](#-example-usage)
- [Tech Stack](#-tech-stack)
- [Security Notes](#-security-notes)
- [Contributing](#-contributing)
- [License](#-license)
- [Credits](#-credits)

## ✨ Features

- **Galaxy Tool Recommendation** – Suggest relevant Galaxy tools for a given bioinformatics task
- **Workflow Recommendation** – Recommend publicly available **Galaxy workflows** (from GitHub) with descriptions, scores, and download links
- **Secure Configuration** – Uses `.env` for API keys and `config.py` for paths
- **Unified Recommendation Endpoint** – `/recommend` merges tool & workflow suggestions in one API call
- **Gemini-powered Query Classification** – Automatically determines if a query is about tools, workflows, or both
- **Structured JSON Responses** – Easy to consume for frontend or third-party applications
- **FastAPI Backend** – RESTful API endpoints for easy integration with frontend or other services
- **Embeddings-based Search** – Uses `intfloat/e5-large` for semantic search

## 🏗️ Architecture

```
Client → [Merged FastAPI endpoint] → [Gemini "classifier" layer]
       ↙                                      ↘
  ToolSuggestionAgent -------------------->  WorkflowSuggestionAgent
                    ↘                         ↙
                       Summarizers (optional)
                                ↓
                           API Response
```

### Workflow

1. Client sends a natural-language query to **`/recommend`**
2. **Gemini classifier** analyzes whether the query relates to:
   - **Tools**
   - **Workflows**
   - **Both**
3. Routes the query to:
   - `ToolSuggestionAgent`
   - `WorkflowSuggestionAgent`
   - or both
4. Returns a **unified JSON response**

## 🚀 Quick Start

### 1️⃣ Prerequisites

- **Python** 3.9+
- **Galaxy API Key** – Create one from [https://usegalaxy.eu/](https://usegalaxy.eu/) (User → Preferences → API Key)
- **GitHub Personal Access Token** – For higher GitHub API rate limits
- **Gemini API Key** – For advanced LLM-based analysis (optional)

### 2️⃣ Installation

Clone and set up the environment:

```bash
git clone https://github.com/iCog-Labs-Dev/galaxy-agent-xp-II.git
cd galaxy-agent-xp-II

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ Configuration

#### Environment Variables

Create a `.env` file in the project root:

```bash
# Create a .env file and copy this in it

GALAXY_URL='https://usegalaxy.eu/'
GALAXY_API_KEY='GALAXY_API_KEY_HERE'        # Replace with your Galaxy API key
GEMINI_API_KEY='YOUR_GEMINI_API_KEY_HERE'   # Replace with your Gemini API key
GITHUB_TOKEN='YOUR_GITHUB_TOKEN_HERE'       # GitHub personal access token for higher rate limits
```

#### Application Configuration

Update `configs/config.py` if you want to customize paths:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_to_encode_path: str = "data/tools_metadata.json"  # Raw Galaxy tools metadata
    embeddings_path: str = "embeddings/galaxy_embeddings.npy"  # Precomputed embeddings
    metadata_path: str = "embeddings/galaxy_metadata.json"      # Cleaned metadata for lookup
```

### 4️⃣ Data Preparation & Embeddings

#### Fetch Galaxy Tools & Workflows

```bash
# Fetch and preprocess Galaxy tools metadata
python utilities/tools_metadata_downloader/run.py

# Fetch and preprocess publicly available workflows
python utilities/workflow_downloader/run.py
```

#### Generate Embeddings

Generate embeddings for semantic search:

```bash
# Embed tools
python agents/scripts/embed_tools.py --input utilities/tools_metadata_downloader/data/preprocessed_tools_{timestamp}.json

# Embed workflows
python agents/scripts/embed_workflows.py --input utilities/workflow_downloader/data/preprocessed_workflows_{timestamp}.json
```

> **Note:** Update `config.py` to point to the generated embedding and metadata files.

### 5️⃣ Run the FastAPI Backend

```bash
uvicorn agents.app:app --reload
```

Server runs at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## ⚡ API Endpoints

### Health Check

**GET** `/health`

**Response:**
```json
{"status": "ok"}
```

### Tool Recommendation

**POST** `/suggest-tools`

**Request:**
```json
{
  "query": "align sequences to a reference genome",
  "top_k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "toolshed.g2.bx.psu.edu/repos/devteam/bwa/bwa_mem/0.7.17.2",
      "name": "BWA-MEM",
      "description": "Align sequences to a reference genome",
      "help": "Performs sequence alignment using BWA-MEM algorithm",
      "category": "Alignment",
      "version": "0.7.17.2",
      "score": 0.92
    }
  ]
}
```

### Workflow Recommendation

**POST** `/suggest-workflows`

**Request:**
```json
{
  "query": "bacterial genome assembly pipeline",
  "top_k": 3
}
```

**Response:**
```json
{
  "results": [
    {
      "name": "bacterial-genome-assembly",
      "category": "genome-assembly",
      "tools_used": ["Shovill", "Bandage Info", "Bandage Image", "ToolDistillator", "ToolDistillator Summarize"],
      "download_url": "https://usegalaxy.eu/api/workflows/xxxx",
      "readme_excerpt": "Bacterial genome assembly workflow for paired end data...",
      "score": 0.8218
    }
  ]
}
```

### Unified Recommendation Endpoint

**POST** `/recommend`

Simpler endpoint where users **don't need to specify** if their query is about **tools** or **workflows**. Gemini will **classify the query** and return the appropriate response.

**Request Body:**
```json
{
  "query": "I want to perform RNA-seq alignment",
  "top_k": 5
}
```

**Possible Responses:**

- **If Gemini detects a Tool query**
```json
"tool_results": [...]
```

- **If Gemini detects a Workflow query**
```json
"workflow_results": [...]
```

- **If Gemini detects Both**
```json
{
  "type": "both",
  "tool_results": [...],
  "workflow_results": [...]
}
```

## 🧩 How It Works

1. **Data Collection**
   - Galaxy tools fetched via [BioBlend](https://bioblend.readthedocs.io/)
   - Public workflows retrieved from [Galaxy IWC GitHub](https://github.com/galaxyproject/iwc)

2. **Embedding & Indexing**
   - Tools & workflows metadata converted to vector embeddings using **intfloat/e5-large** or **Gemini Embeddings**

3. **AI-Powered Search**
   - User queries converted to embeddings
   - Cosine similarity search finds the most relevant tools and workflows

4. **FastAPI Service**
   - Single API layer to handle requests from frontend or CLI

5. **Gemini Classification**
   - The internal Gemini layer classifies the query into **tool**, **workflow**, or **both** before routing

## 📌 Key Notes

- **Independent Use:** You can still call `/tools/suggest` and `/workflows/suggest` independently if you already know the type of query
- **Merged Endpoint:** `/recommend` is ideal for **frontend clients** or **end users** who simply provide a natural-language query

## 🧪 Example Usage

After starting the FastAPI server:

```bash
curl -X POST "http://127.0.0.1:8000/suggest-tools" \
    -H "Content-Type: application/json" \
    -d '{"query":"RNA sequencing analysis","top_k":3}'
```

## 🧩 Tech Stack

- **FastAPI** – Backend API
- **Gemini LLM** – Query classification
- **BioBlend** – Communication with Galaxy API
- **Galaxy Platform** – Public instance: [usegalaxy.eu](https://usegalaxy.eu)

## 🛡️ Security Notes

- **Never commit** your real `.env` file to GitHub
- Use the provided **sample** as a template only
- For production, use **environment variable secrets** or a vault service

## 🤝 Contributing

Pull requests are welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Submit a PR with a clear description

## 📜 License

MIT License – Feel free to use and modify

## 💡 Credits

- [Galaxy Project](https://galaxyproject.org/)
- [BioBlend](https://bioblend.readthedocs.io/en/latest/)
- [Sentence Transformers](https://www.sbert.net/)
- [Google Gemini](https://deepmind.google/technologies/gemini/)

---