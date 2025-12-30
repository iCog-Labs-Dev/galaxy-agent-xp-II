VENV_NAME := venv
REQUIREMENTS := requirements.txt

PY := python3
CSV_DIR := agents/generic_loader/data

# Pick the latest downloaded JSONs if present; tolerate missing files.
TOOLS_JSON ?= $(shell ls -1t utilities/tools_metadata_downloader/data/galaxy_instance_tools_*.json 2>/dev/null | head -1)
WORKFLOW_JSON ?= $(shell ls -1t utilities/workflow_downloader/data/iwc_full_*.json 2>/dev/null | head -1)

NEO4J_URI ?= bolt://localhost:7687
NEO4J_USER ?= neo4j
# NEO4J_PASSWORD should be provided in the environment or via CLI: make load_graph NEO4J_PASSWORD=...

activate:
	@echo "Setting up virtual environment..."
	 python3 -m venv $(VENV_NAME) && \
	 . $(VENV_NAME)/bin/activate && \
	 pip install --upgrade pip && \
	 pip install -r $(REQUIREMENTS)
	@echo "\nVirtual environment ready. To activate manually:"
	@echo "source $(VENV_NAME)/bin/activate"

fetch_tools:
	python3 tool_downloader.py

tools_csv:
	@if [ -n "$(TOOLS_JSON)" ]; then \
		echo "Using tools JSON: $(TOOLS_JSON)"; \
		$(PY) agents/generic_loader/convert_tools_json_to_csv.py $(TOOLS_JSON) --output-dir $(CSV_DIR); \
	else \
		echo "Skipping tools_csv: no tools JSON found in utilities/tools_metadata_downloader/data"; \
	fi

workflows_csv:
	@if [ -n "$(WORKFLOW_JSON)" ]; then \
		echo "Using workflow JSON: $(WORKFLOW_JSON)"; \
		$(PY) agents/generic_loader/convert_json_to_csv.py $(WORKFLOW_JSON) --output-dir $(CSV_DIR); \
	else \
		echo "Skipping workflows_csv: no workflow JSON found in utilities/workflow_downloader/data"; \
	fi

load_graph:
	@if [ -z "$(NEO4J_PASSWORD)" ]; then echo "NEO4J_PASSWORD is required"; exit 1; fi
	$(PY) agents/generic_loader/generic_csv_loader.py \
		--csv-dir $(CSV_DIR) \
		--uri $(NEO4J_URI) \
		--user $(NEO4J_USER) \
		--password "$(NEO4J_PASSWORD)"

# Full pipeline: convert latest tools/workflows to CSV then load
pipeline: tools_csv workflows_csv load_graph

.PHONY: activate fetch_tools tools_csv workflows_csv load_graph pipeline


.PHONY: activate fetch_tools
