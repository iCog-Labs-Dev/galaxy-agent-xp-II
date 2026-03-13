# Workflow Generator

This module generates Galaxy workflows using AI-based tool sequence prediction and validation.

## Overview
- Predicts a sequence of tools for a workflow using a trained transformer model.
- Validates tool availability on the Galaxy instance.
- Assembles a .ga workflow file for import into Galaxy.

## Main Components
- `run_workflow_generator.py`: Entry point for generating workflows.
- `generator.py`: Predicts tool sequences using the model.
- `generate_ga_file.py`: Builds the Galaxy workflow JSON (.ga file).
- `validator.py`: Validates tool availability and updates tool mapping.
- `create_tool_dict.py`: Generates bridge dictionary from workflow connections.

## Usage
1. Set up your environment and install dependencies (see requirements.txt).
2. Configure Galaxy API credentials in a `.env` file:
   ```
   GALAXY_URL=http://localhost:8080
   GALAXY_API_KEY=your_api_key
   OPENAI_API_KEY=your_openai_key      # optional, for OpenAI reranking
   GEMINI_API_KEY=your_gemini_api_key  # optional, for Gemini reranking
   ```
3. Run in hybrid mode (default):
   ```bash
   python agents/expriments/workflow_generator/run_workflow_generator.py \
     --mode hybrid \
     --seed_tool Grep1 \
     --max_steps 15 \
     --top_k 8 \
     --top_p 0.9 \
     --temperature 1.0
   ```
    Hybrid with Gemini reranking:
    ```bash
    python agents/expriments/workflow_generator/run_workflow_generator.py \
       --mode hybrid \
       --llm_provider gemini \
       --llm_model gemini-1.5-flash
    ```
4. Run transformer-only mode:
   ```bash
   python agents/expriments/workflow_generator/run_workflow_generator.py --mode transformer
   ```
5. Disable LLM reranking in hybrid mode:
   ```bash
   python agents/expriments/workflow_generator/run_workflow_generator.py --mode hybrid --disable_llm
   ```
6. Skip Galaxy validation if your instance is unavailable/slow:
   ```bash
   python agents/expriments/workflow_generator/run_workflow_generator.py --mode hybrid --skip_validation
   ```
7. Set Galaxy API timeout (seconds):
   ```bash
   python agents/expriments/workflow_generator/run_workflow_generator.py --mode hybrid --galaxy_timeout 10
   ```
8. Save detailed LLM/score trace (JSON):
   ```bash
   python agents/expriments/workflow_generator/run_workflow_generator.py \
     --mode hybrid \
     --llm_provider gemini \
     --llm_model gemini-2.5-flash \
     --llm_trace_file agents/expriments/reports/workflow_generator/llm_trace.json
   ```
9. Print full trace to console:
    ```bash
    python agents/expriments/workflow_generator/run_workflow_generator.py \
       --mode hybrid \
       --llm_provider gemini \
       --llm_model gemini-2.5-flash \
       --console_trace
    ```
10. Import the generated `ai_generated_workflow.ga` file into Galaxy.

11. If Galaxy import shows many missing required params, run safe mode:
    ```bash
    python agents/expriments/workflow_generator/run_workflow_generator.py \
       --mode hybrid \
       --safe_mode
    ```

## Runtime options
- `--mode`: `hybrid` (transformer + optional LLM rerank) or `transformer`
- `--seed_tool`: first tool in the generated workflow
- `--max_steps`: max generated chain length
- `--top_k`, `--top_p`, `--temperature`: candidate diversity controls
- `--repetition_penalty`: discourages repeating already used tools
- `--llm_provider`: `auto`, `openai`, or `gemini`
- `--llm_model`: model name for the selected provider (default `gpt-4o-mini`)
- `--disable_llm`: keeps hybrid loop but uses heuristic reranking only
- `--skip_validation`: bypasses Galaxy installed-tools verification
- `--galaxy_timeout`: timeout in seconds for Galaxy API tool fetch
- `--llm_trace_file`: writes per-step candidates, model probabilities, heuristic scores, LLM pick, and chosen tool
- `--console_trace`: prints the same detailed per-step trace directly in terminal
- `--safe_mode`: removes tools likely to fail automatic import due to complex parameters/multi-input requirements
- `--workflow_name`, `--output_file`: output metadata and filename

## Directory Structure
```
workflow_generator/
├── create_tool_dict.py
├── generator.py
├── generate_ga_file.py
├── run_workflow_generator.py
├── validator.py
```

## Requirements
- Python 3.8+
- TensorFlow
- h5py
- python-dotenv
- bioblend

## Notes
- Only tools installed on Galaxy will be included in the generated workflow.

## Backend API Integration

The workflow generator now includes a FastAPI backend for programmatic workflow generation and .ga file download.

### API Endpoints
- `/generate-workflow-transformer`: Generate a workflow using the transformer model.
- `/generate-workflow-hybrid`: Generate a workflow using hybrid (transformer + LLM) mode.
- `/download-workflow-ga`: Generate and download a Galaxy .ga workflow file. Filename includes LLM-generated workflow name, version, and timestamp.

### Features
- LLM integration (Gemini 2.5 Flash) for workflow naming.
- .ga file saving with version and timestamp for traceability.
- Workflow name and version set in JSON.

### Example API Requests and Responses

#### Transformer Mode
Request:
```
POST /generate-workflow-transformer
{
  "seed_tool": "Grep1",
  "max_steps": 15
}
```
Response:
```
{
  "Generated Workflow": "Grep1 -> tp_cat -> tp_easyjoin_tool -> join1 -> tp_sort_header_tool -> Add_a_column1 -> tp_cut_tool -> Grouping1 -> addValue -> datamash_ops -> tp_replace_in_column -> bedtools_intersectbed -> Convert characters1 -> Remove beginning1 -> tab2fasta"
}
```

#### Hybrid Mode (Transformer + LLM)
Request:
```
POST /generate-workflow-hybrid
{
  "seed_tool": "tp_easyjoin_tool",
  "max_steps": 15
}
```
Response:
```
{
  "Generated Workflow": "tp_easyjoin_tool -> tp_cat -> featurecounts -> tp_sort_header_tool -> join1 -> Add_a_column1 -> tp_cut_tool -> bedtools_intersectbed -> Grouping1 -> addValue -> datamash_ops -> tp_replace_in_column -> Convert characters1 -> Remove beginning1"
}
```

See `app.py` for implementation details.
