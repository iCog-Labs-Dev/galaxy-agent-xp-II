# Next-Tool-Recommendation

FastAPI service for recommending the next Galaxy tool from a tool sequence.

## Folder Structure

- `app.py` - FastAPI app and endpoints
- `model.py` - transformer model + model manager
- `utils.py` - parsing, alias resolution, prediction utilities
- `config.py` - local settings (`MODEL_PATH`, `MAX_SEQ_LEN`, `TOP_K_DEFAULT`)
- `tests/` - unit and API tests
- `tests/data/test_data.json` - real sequence-based test payloads

## Requirements

- Python 3.10+
- Virtual environment with dependencies installed from project root `requirements.txt`
- Model file available at path configured in `config.py`

## Run the API

From project root:

```bash
source venv/bin/activate
cd agents/expriments/Next-Tool-Recommendation
uvicorn app:app --reload
```

Open docs at:

- `http://127.0.0.1:8000/docs`

## Endpoints

### `GET /`
Health endpoint.

Example response:

```json
{
  "status": "ok",
  "service": "Tool Recommendation API"
}
```

### `POST /Next Tool Recommendation`
Predict next tools from a comma-separated sequence.

Request body:

```json
{
  "tool_sequence": "porechop,fastp,fastqc",
  "topk": 5
}
```

Response body:

```json
{
  "Input Sequence Of Tools": "Input,toolshed.g2.bx.psu.edu/repos/iuc/porechop/porechop/0.2.4+galaxy1",
  "Next Tool Recommendations": [
    {
      "Tool_Name": "fastqc",
      "Tool_Score": 0.575
    }
  ]
}
```



## Run Tests

From project root:

```bash
source venv/bin/activate
pytest agents/expriments/Next-Tool-Recommendation/tests -q
```
