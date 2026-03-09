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
   ```
3. Run the generator:
   ```bash
   python -m agents.expriments.workflow_generator.run_workflow_generator
   ```
4. Import the generated `ai_generated_workflow.ga` file into Galaxy.

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
