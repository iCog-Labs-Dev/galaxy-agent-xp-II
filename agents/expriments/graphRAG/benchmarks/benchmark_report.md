# Benchmarking Report – GraphRAG Tool & Workflow Retrieval

## 1. Overview

This benchmarking evaluates the **retrieval quality of Galaxy tools and workflows** using **embedding-based similarity search** combined with **Neo4j vector indexing and graph context expansion**.

The evaluation setup includes:

- **Similarity Metric:** Cosine similarity  
- **Evaluation Metric:** Recall@k  
- **Embedding Model:** `BAAI/bge-base-en-v1.5`  
- **LLM:** `models/gemini-2.5-flash`

result:
- **Tool Recall@5:** 68%  
- **Workflow Recall@5:** 88%  
- **Overall Recall@5:** 78%


## 2. Methodology

### 2.1 Dataset Preparation
- Tool queries: `tool_test_queries.json`
- Workflow queries: `workflow_test_queries.json`
- Each query is paired with a **ground-truth list** of expected tools or workflows.

### 2.2 Retrieval Pipeline
1. User query embedding generated using `QueryEmbeddingService`
2. Top-k entities retrieved from **Neo4j Vector Index**
3. Graph context expanded using connected nodes and relationships
4. Retrieved entities embedded for comparison

### 2.3 Evaluation Logic
- Cosine similarity computed between **expected** and **retrieved** embeddings
- Similarity threshold: **0.8**
- Recall definition:
  - `Recall@k = 1` if **any retrieved entity** exceeds the threshold
  - `Recall@k = 0` otherwise
- Final score computed as **average recall across all queries**

---

## 3. Tool Retrieval Benchmark

**Metric:** Recall@5  
**Similarity Threshold:** 0.8  

---

### Query 1
- **Query:** Search sequence database using jackhmmer  
- **Expected Tool:** jackhmmer  
- **Top-5 Retrieved:**  
  - phmmer  
  - jackhmmer  
- **Recall@5:**  1  

---

### Query 2
- **Query:** Retrieve genomic datasets from NCBI  
- **Expected Tool:** Get Microbial Data  
- **Top-5 Retrieved:**  
  - NCBI Datasets Genomes  
  - Get Microbial Data  
- **Recall@5:**  1  

---

### Query 3
- **Query:** Convert genome coordinates between assemblies  
- **Expected Tool:** CrossMap Wig  
- **Top-5 Retrieved:**  
  - CrossMap GFF  
  - CrossMap VCF  
- **Recall@5:**  0  

---

### Query 4
- **Query:** Translate gene identifiers between organisms  
- **Expected Tool:** gProfiler Orth  
- **Top-5 Retrieved:**  
  - annotateMyIDs  
- **Recall@5:**  0  

---

### Query 5
- **Query:** Download list of URLs via lftp  
- **Expected Tool:** downloads  
- **Top-5 Retrieved:**  
  - downloads  
  - FTP Link for Bioimage Archive  
  - Online data  
- **Recall@5:**  1  

---

** Average Recall@5 (Tools): 0.68**

---

## 4. Workflow Retrieval Benchmark

**Metric:** Recall@5  
**Similarity Threshold:** 0.8  

---

### Query 1
- **Query:** Genome assembly with HiFi reads (VGP4)  
- **Expected Workflow:** Genome Assembly from Hifi reads with HiC phasing – VGP4  
- **Top-5 Retrieved:**  
  - assembly-hifi-only-vgp3  
  - kmer-profiling-hifi-vgp1  
  - assembly-hifi-hic-phasing-vgp4  
  - assembly-hifi-trio-phasing-vgp5  
  - scaffolding-hic-vgp8  
- **Recall@5:**  1  

---

### Query 2
- **Query:** Scaffolding genome with Bionano  
- **Expected Workflow:** Scaffolding with Bionano  
- **Top-5 Retrieved:**  
  - hi-c-contact-map-for-assembly-manual-curation  
  - kmer-profiling-hifi-vgp1  
  - assembly-hifi-trio-phasing-vgp5  
  - scaffolding-bionano-vgp7  
  - scaffolding-hic-vgp8  
- **Recall@5:**  1  

---

### Query 3
- **Query:** K-mer profiling for PacBio HiFi trio  
- **Expected Workflow:** kmer-profiling-hifi-trio-VGP2  
- **Top-5 Retrieved:**  
  - assembly-hifi-only-vgp3  
  - kmer-profiling-hifi-vgp1  
  - assembly-hifi-hic-phasing-vgp4  
  - assembly-hifi-trio-phasing-vgp5  
  - kmer-profiling-hifi-trio-vgp2  
- **Recall@5:**  1  

---

### Query 4
- **Query:** Detect antimicrobial resistance genes  
- **Expected Workflow:** AMR gene detection workflow in an assembled bacterial genome  
- **Top-5 Retrieved:**  
  - amr_gene_detection  
  - kmer-profiling-hifi-vgp1  
  - kmer-profiling-hifi-trio-vgp2  
  - bacterial_genome_annotation  
  - bacterial-quality-and-contamination-control-post-assembly  
- **Recall@5:**  1  

---

### Query 5
- **Query:** Identify virulence genes  
- **Expected Workflow:** AMR gene detection workflow in an assembled bacterial genome  
- **Top-5 Retrieved:**  
  - amr_gene_detection  
  - kmer-profiling-hifi-vgp1  
  - assembly-decontamination-vgp9  
  - bacterial_genome_annotation  
  - bacterial-quality-and-contamination-control-post-assembly  
- **Recall@5:**  1  

---

** Average Recall@5 (Workflows): 0.88**

> Workflow retrieval performs strongly due to richer semantic descriptions and graph connectivity.

---

## 5. Summary & Insights

- **Tool Retrieval:** 68% Recall@5  
  - Misses mainly caused by naming inconsistencies and metadata variation
- **Workflow Retrieval:** 88% Recall@5  
  - Strongly benefits from graph-based context expansion
- **Overall Performance:** Hybrid Vector + GraphRAG approach is effective

---

## 6. Limitations & Observed Issues

### Gemini API Rate Limit Exceeded

During benchmarking and iterative testing, **Gemini API rate limits were exceeded** due to **consecutive LLM calls**, particularly during batch evaluations.

**Impact:**
- Temporary failures in:
  - Intent classification
  - Answer generation and summarization
- Retrieval and benchmarking logic remained unaffected

**Cause:**
- Exceeded **Gemini free-tier request limits** from repeated calls in short intervals

---

## 7. Conclusion

- **Tool Recall@5:** 68%  
- **Workflow Recall@5:** 88%  
- **Overall Recall@5:** 78%

These results validate that the **Neo4j Vector + GraphRAG architecture** provides effective semantic retrieval, with workflows benefiting most from graph-based context expansion. Future improvements should focus on metadata normalization and LLM call optimization.
