# GRU tool-sequence experiment

This folder contains a notebook experiment that learns to predict the next tool in a workflow using a GRU model.

## What the data is

The TSV file in [agents/expriments/data/worflow-connection-20-04.tsv](agents/expriments/data/worflow-connection-20-04.tsv) stores workflow step connections. Each row represents a directed edge from a source step to a target step with tool names and versions.

## What the notebook does

The notebook [agents/expriments/GRU_expriment.ipynb](agents/expriments/GRU_expriment.ipynb) follows these steps:

1. **Load the TSV**
   - Reads the TSV without a header row and assigns inferred column names.
   - Converts IDs to numeric and cleans invalid rows.

2. **Build tool sequences per workflow**
   - Groups rows by `workflow_id`.
   - Builds a per-workflow DAG of steps and performs a topological sort.
   - Converts the ordered step list into a tool-name sequence.

3. **Prepare training samples**
   - Builds a vocabulary over tools.
   - Uses a fixed-length context window (default 5).
   - Creates `(context -> next tool)` training pairs.

4. **Train a GRU**
   - Embedding + GRU + linear classifier.
   - Trains for a few epochs (configurable).

5. **Predict next tools**
   - Given a context of tools, outputs top‑k next-tool predictions.

## How to run

Open the notebook and run all cells in order:

- [agents/expriments/GRU_expriment.ipynb](agents/expriments/GRU_expriment.ipynb)

## Key knobs to tune

- `sample_size`: number of workflows used to build sequences.
- `context_len`: number of previous tools used to predict the next tool.
- `max_samples`: maximum training pairs used for training speed.
- `epochs`, `embedding_dim`, `hidden_dim`: model capacity and training budget.

## Notes

- If you want higher accuracy, increase `sample_size`, `max_samples`, and `epochs`.
- The current preprocessing uses a simple topological ordering for each workflow DAG.