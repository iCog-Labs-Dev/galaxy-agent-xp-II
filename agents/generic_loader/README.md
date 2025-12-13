# Generic Loader

A reusable, config-driven pipeline to convert scraped workflow JSON into CSVs and load them into Neo4j. Designed to be schema-flexible so it can ingest workflows, tools, and future datasets without hardcoding labels and relationships.

## Components
- `convert_json_to_csv.py`: Flattens IWC workflow JSON into multiple CSVs.
  - Outputs:
    - `workflows.csv`: top-level workflow flags and README content
    - `workflow_files.csv`: per workflow file (name, steps count, URL)
    - `workflow_steps.csv`: per step (ids, type, tool info)
    - `step_inputs.csv`: per step input definition
    - `step_outputs.csv`: per step output definition
    - `step_input_connections.csv`: downstream input → upstream step/output mapping
    - `tools_used.csv`: optional, tool rows derived if not present
- `schema_models.py`: Pydantic models describing dynamic node/relationship config (`NodeSpec`, `RelationshipSpec`, `LoaderConfig`) plus `DEFAULT_CONFIG`.
- `generic_csv_loader.py`: Config-driven CSV → Neo4j loader that merges nodes first, then edges.

## ID Strategy (deterministic)
- `Category`: `category_id = md5(category)`
- `Workflow`: `workflow_id = md5(workflow_repository, file_name)`
- `Step`: `step_uid = md5(workflow_id, step_id)`
- `Input`: `input_uid = md5(workflow_id, step_id, name, description)`
- `Output`: `output_uid = md5(workflow_id, step_id, name, description)`
- `Tool`: `tool_id = id`

## Relationships
- `Category` -[:HAS_WORKFLOW]-> `Workflow`
- `Workflow` -[:HAS_STEP {step_id}]-> `Step`
- `Step` -[:STEP_REQUIRES]-> `Input`
- `Step` -[:STEP_GENERATES]-> `Output`
- `Output` -[:FEEDS_INTO {to_input, source_type='Output', target_type='Input'}]-> `Input`
- `Workflow` -[:WORKFLOW_USES_TOOL]-> `Tool` (optional)

## Usage
1) Generate CSVs from IWC JSON:
```bash
python agents/generic_loader/convert_json_to_csv.py \
  utilities/workflow_downloader/data/iwc_full_20251127_094915.json \
  --output-dir agents/generic_loader/data
```

2) Load CSVs into Neo4j:
```bash
python agents/generic_loader/generic_csv_loader.py \
  --csv-dir agents/generic_loader/data \
  --uri bolt://localhost:7687 \
  --user neo4j \
  --password YOUR_PASSWORD
```

## Customization
- Edit `DEFAULT_CONFIG` in `schema_models.py` to add new entities or edges.
- Add `NodeSpec` for a new label: set `file`, `id_fields`, `id_property`, `prop_fields`.
- Add `RelationshipSpec` to connect nodes: set `type`, `file`, `from_`, `to`, endpoint `id_fields`, and optional `prop_fields`, `set_source_target`.

## Notes
- Loader is idempotent (MERGE + deterministic IDs).
- Input connections are materialized as edges (`FEEDS_INTO`) for traversal.
- The loader reads only the CSVs referenced by the active config.