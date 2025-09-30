# Embedding Generation Scripts

This directory contains scripts for generating text embeddings for Galaxy tools and workflows metadata using SentenceTransformer models.

## Overview

The embedding scripts convert structured metadata from Galaxy tools and workflows into vector embeddings that enable semantic search functionality in the Galaxy Agent XP-II system.

## Scripts

### 1. Workflow Embedding Generator (`embed_workflows.py`)

Generates embeddings for Galaxy workflow metadata from the Intergalactic Workflow Commission (IWC) repository.

#### Usage
```bash
python embed_workflows.py --input path/to/preprocessed_workflows.json [--output-dir agents/embeddings] [--model intfloat/e5-base-v2]
```

#### Features
- Processes workflow metadata including repository, category, description, tools used, and download URLs
- Creates structured text combining all workflow information for embedding
- Saves both embeddings and complete metadata with timestamps
- Includes download URLs in both embedded text and saved metadata

#### Output Files
- `iwc_workflow_embeddings_YYYYMMDD_HHMMSS.npy` - NumPy array of embeddings
- `iwc_workflow_metadata_YYYYMMDD_HHMMSS.json` - Complete workflow metadata with download URLs

### 2. Tool Embedding Generator (`embed_tools.py`)

Generates embeddings for Galaxy tools metadata from BioBlend API responses.

#### Usage
```bash
python embed_tools.py --input path/to/preprocessed_tools.json [--output-dir agents/embeddings] [--model intfloat/e5-base-v2]
```

#### Features
- Processes tool metadata including ID, name, description, categories, version, and help text
- Safely handles null values and missing fields
- Combines multiple metadata fields into a single descriptive text for embedding
- Automatic timestamp versioning for output files

#### Output Files
- `galaxy_embeddings_YYYYMMDD_HHMMSS.npy` - NumPy array of embeddings
- `galaxy_metadata_YYYYMMDD_HHMMSS.json` - Original tool metadata

## Required Dependencies

```python
sentence-transformers >= 2.2.2
numpy >= 1.21.0
torch >= 1.9.0
transformers >= 4.20.0
```

## Model Options

Both scripts support any SentenceTransformer model. Default models:

- **Workflows**: `intfloat/e5-base-v2`
- **Tools**: `intfloat/e5-base-v2`

### Alternative Models
- `intfloat/e5-large-v2` - Higher quality, larger model
- `all-mpnet-base-v2` - General purpose model
- `all-MiniLM-L6-v2` - Faster, smaller model

## Input Data Format

### Workflows JSON Format
```json
[
  {
    "workflow_repository": "repository/name",
    "category": "genome-assembly",
    "readme_cleaned": "Workflow description...",
    "tool_names": ["tool1", "tool2"],
    "raw_download_url": "https://raw.githubusercontent.com/.../workflow.ga"
  }
]
```

### Tools JSON Format
```json
[
  {
    "id": "toolshed.g2.bx.psu.edu/repos/devteam/bwa",
    "name": "BWA",
    "description": "Burrows-Wheeler Aligner",
    "categories": ["NGS", "Alignment"],
    "version": "0.7.17",
    "help": "Tool help text..."
  }
]
```

## Text Construction for Embedding

### Workflows
```
"Workflow Repository: {repo}. Category: {category}. Description: {readme}. Tools Used: {tools}. Download URL: {url}"
```

### Tools
```
"{tool_id} - {name} - {description} - {categories} - {version} - {help}"
```

## Integration with Galaxy Agent

After generating embeddings, update the configuration in `config.yml`:

```python
class Settings(BaseSettings):
    embeddings_path: str = "embeddings/galaxy_embeddings_20240101_120000.npy"
    metadata_path: str = "embeddings/galaxy_metadata_20240101_120000.json"
    workflow_embeddings_path: str = "embeddings/iwc_workflow_embeddings_20240101_120000.npy"
    workflow_metadata_path: str = "embeddings/iwc_workflow_metadata_20240101_120000.json"
```

## Example Usage

### Generate Workflow Embeddings
```bash
python embed_workflows.py \
    --input utilities/workflow_downloader/data/preprocessed_workflows_20240101_120000.json \
    --output-dir agents/embeddings \
    --model intfloat/e5-base-v2
```

### Generate Tool Embeddings
```bash
python embed_tools.py \
    --input utilities/tools_metadata_downloader/data/preprocessed_tools_20240101_120000.json \
    --output-dir agents/embeddings \
    --model intfloat/e5-large-v2
```

## Performance Notes

- **Memory Usage**: Larger models like `e5-large-v2` require more RAM
- **Processing Time**: ~1000 records/minute on CPU, significantly faster on GPU
- **Output Size**: Embeddings are typically 384-1024 dimensions depending on model

## Troubleshooting

1. **Memory Errors**: Use smaller models or process in batches
2. **Model Download Issues**: Check internet connection and firewall settings
3. **JSON Format Errors**: Validate input JSON files before processing
4. **Output Directory**: Ensure write permissions for the output directory