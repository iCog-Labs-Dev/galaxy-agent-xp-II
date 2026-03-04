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
  "Input Sequence Of Tools": "porechop,fastp,fastqc",
  "Next Tool Recommendations": [
    {
      "Tool_Name": "tp_cat",
      "Tool_Score": 0.696
    },
    {
      "Tool_Name": "featurecounts",
      "Tool_Score": 0.665
    },
    {
      "Tool_Name": "cat1",
      "Tool_Score": 0.612
    },
    {
      "Tool_Name": "samtools_view",
      "Tool_Score": 0.555
    },
    {
      "Tool_Name": "multiqc",
      "Tool_Score": 0.549
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
