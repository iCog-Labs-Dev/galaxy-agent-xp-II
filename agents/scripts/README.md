# Embedding Scripts for Tools & Workflows

This directory contains Python scripts to generate embeddings for **Galaxy tools** and **IWC workflows** using the [`intfloat/e5-base-v2`](https://huggingface.co/intfloat/e5-base-v2) Sentence Transformer model.  
The embeddings and metadata are saved for later use in retrieval, similarity search, or downstream ML tasks.


## Scripts

### 1. Tool Embeddings
**File:** `agents/scripts/generate_tool_embeddings.py`  

Encodes Galaxy tool metadata into vector embeddings.  

**Arguments:**
- `--input` (str, required): Path to the tool metadata JSON file.  
- `--output_dir` (str, default: `agents/embeddings`): Directory where embeddings and metadata will be stored.  
- `--model` (str, default: `BAAI/bge-base-en-v1.5`): Hugging Face model to use for encoding.  

**Run Example:**
```bash
python agents/scripts/generate_tool_embeddings.py \
  --input agents/data/galaxy_tools_metadata.json \
  --output_dir agents/embeddings \
  --model BAAI/bge-base-en-v1.5
```
For the workflows we do the same thing as below we run our script with dynamic path
```
python agents/scripts/generate_workflow_embeddings.py \
  --input agents/data/iwc_workflows_summary_june20_2025.json \
  --output_dir agents/embeddings \
  --model BAAI/bge-base-en-v1.5
```
