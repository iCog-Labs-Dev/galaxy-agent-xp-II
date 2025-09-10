---

# Sentence Embedding with `intfloat/e5-base-v2`

This guide explains how to generate **sentence embeddings** from the validated workflow output produced by:

```
iwc_downloader.py → preprocess_wf_data.py → workflow_schema_validator.py
             ↓                 ↓                        ↓
       Raw GitHub data   →   Cleaned data       →   Validated JSON
```

The **validated JSON** is the final output and will be used as input for embedding.

---

## 1. Install Dependencies

Make sure the required libraries are installed:

```bash
pip install sentence-transformers torch
```

---

## 2. Load the Embedding Model

We use the [E5 model family](https://huggingface.co/intfloat/e5-base-v2), which is optimized for text embedding tasks.

```python
from sentence_transformers import SentenceTransformer

# Load the model
model = SentenceTransformer("intfloat/e5-base-v2")
```

---

## 3. Load Validated Data

The validated workflows are stored as JSON in the `data/` directory (produced by the pipeline). Example:

```python
import json

validated_file = "utilities/workflow_downloader/data/validated_workflows.json"

with open(validated_file, "r") as f:
    workflows = json.load(f)
```

Each entry in the JSON corresponds to a cleaned and validated workflow object.

---

## 4. Prepare Text for Embedding

Decide what textual information you want to embed. Common options:

- Workflow `workflow_name`
- Workflow `category`
- Workflow `description` (if available)

Example:

```python
texts = []
for wf in workflows:
    name = wf.get("workflow_name", "")
    category = wf.get("category", "")
    description = wf.get("description", "")

    # Combine fields into a single string
    text_input = f"{name} | {category} | {description}"
    texts.append(text_input)
```

---

## 5. Generate Embeddings

Pass the prepared text into the embedding model:

```python
embeddings = model.encode(texts, convert_to_tensor=True, show_progress_bar=True)
```

- `texts` → list of workflow descriptions
- `embeddings` → tensor of shape `(num_workflows, 768)` for `e5-base-v2`

---

## 6. Store or Use Embeddings

You can store embeddings for later use (search, clustering, etc.):

```python
import numpy as np

np.save("workflow_embeddings.npy", embeddings.cpu().numpy())
```

Or integrate directly into downstream tasks (e.g., similarity search, semantic clustering, retrieval).

---

## 7. Example: Find Similar Workflows

```python
from sentence_transformers.util import cos_sim

# Compare the first workflow to all others
similarities = cos_sim(embeddings[0], embeddings)[0]

# Get top 5 most similar workflows
top_indices = similarities.argsort(descending=True)[:5]

for idx in top_indices:
    print(texts[idx], "→", similarities[idx].item())
```

---

## Summary

- Run the pipeline to generate **validated JSON**.
- Use `intfloat/e5-base-v2` to convert workflow text into dense vector embeddings.
- Save and use embeddings for tasks such as **semantic search**, **clustering**, or **recommendation**.

---
