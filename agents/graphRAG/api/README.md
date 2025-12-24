# GraphRAG Retrieval API

FastAPI service for retrieving workflows and tools with intent detection and LLM synthesis.

## Features

- **Intent Detection**: Automatically detects if user query is about workflows, tools, or both
- **Workflow Retrieval**: Vector search + graph traversal for workflows
- **Tool Retrieval**: Vector search + graph traversal for tools
- **LLM Synthesis**: Uses Gemini LLM to synthesize natural language answers from retrieved results

## Endpoints

### Main Endpoint

**POST `/query`**
- Detects intent, retrieves workflows/tools, and optionally synthesizes answer
- Request body:
  ```json
  {
    "query": "RNA-seq quality control workflow",
    "top_k": 5,
    "synthesize": true
  }
  ```
- Response:
  ```json
  {
    "intent": "workflow",
    "intent_confidence": 0.85,
    "workflows": [...],
    "tools": null,
    "synthesized_answer": "Based on your query..."
  }
  ```

### Specific Endpoints

**POST `/query-workflows`** - Query workflows only
**POST `/query-tools`** - Query tools only
**POST `/detect-intent`** - Detect intent without retrieval

### Health Check

**GET `/health`** - Check service status

## Running the API

```bash
# Activate virtual environment
source venv10/bin/activate

# Set API key (optional, for LLM synthesis)
export GOOGLE_API_KEY=your_key_here

# Run the API
python agents/graphRAG/api/retrieval_api.py
```

The API will start on `http://localhost:8001`

## Usage Examples

### Python
```python
import requests

response = requests.post(
    "http://localhost:8001/query",
    json={
        "query": "quality control tool for sequencing data",
        "top_k": 5,
        "synthesize": True
    }
)
print(response.json())
```

### cURL
```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "RNA-seq workflow",
    "top_k": 5,
    "synthesize": true
  }'
```

## Architecture

1. **Intent Detection** (`IntentDetector`): Keyword-based classification
2. **Vector Search**: Semantic search using embeddings
3. **Graph Traversal**: Retrieves related nodes (steps, tools, inputs, outputs)
4. **LLM Synthesis**: Combines results into natural language answer

