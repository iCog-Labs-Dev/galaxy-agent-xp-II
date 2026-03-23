# Comparative Report: GRU vs LSTM vs Transformer

**Date:** 2026-03-23

---

## Overview

This report compares the best-performing GRU, LSTM, and Transformer models trained for tool-sequence prediction in the Galaxy Agent project. The comparison focuses **only on metrics shared across all three architectures**.

---

## 1. All GRU Runs

| Run ID | Context Len | Vocab Size | Min Tool Count | Epochs | Best Val Loss | Val Top-1 (%) | Val Top-5 (%) |
|--------|-------------|------------|----------------|--------|---------------|---------------|---------------|
| 20260211_150122 | 5  | 1880 | — | 15 | 0.9599 *(train)* | — | — |
| 20260211_151345 | 5  | 1880 | — | 50 | 0.5415 *(train)* | — | — |
| **20260213_025555** | **5** | **1880** | **—** | **47** | **1.7254** | **70.81** | **85.34** |
| 20260213_030205 | 10 | 762  | 5 | 35 | 2.4037 | 69.94 | 85.27 |
| 20260217_030824 | 20 | 1194 | 3 | 39 | 2.8311 | 70.32 | 84.67 |
| 20260217_033110 | 20 | 1586 | 2 | 31 | 4.6301 | 53.79 | 72.35 |

> **Bold** = best GRU run.

---

## 2. All LSTM Runs

| Stage | Architecture | Embed / Hidden | Dropout | Epochs (Early Stop) | Best Val Loss | Hit@1 (%) | Hit@5 (%) |
|-------|-------------|----------------|---------|---------------------|---------------|-----------|-----------|
| 1 — Baseline | LSTM (default) | — | — | — | — | — | 70.0 |
| **2 — High Capacity** | **Bi-LSTM** | **128 / 256** | **0.3** | **19** | **—** | **—** | **90.0** |
| 3 — Regularized | Uni-LSTM + Mean Pool | 64 / 128 | 0.5 | 34 | 5.699 | 27.1 | 75.0 |
| 4 | — | — | — | — | 5.462 | 25.8 | 42.0 |
| 5 — Refined | Uni-LSTM (Last Hidden) | 256 / 512 | 0.4 | 17 (best@7) | 5.066 | 25.9 | 42.7 |

> **Bold** = best LSTM by Hit@5 (Stage 2).

---

## 3. All Transformer Runs

| Run ID | Embed Dim | Heads | FF Dim | Dropout | Train Iters | Best Test Loss | Test Acc (%) | Precision (%) | Low-Freq Precision (%) |
|--------|-----------|-------|--------|---------|-------------|----------------|--------------|---------------|------------------------|
| **20260227_002159** | **128** | **4** | **128** | **0.2** | **200** | **0.0474** | **97.36** | **36.17** | **3.21** |
| 20260228_040521 | 128 | 4 | 128 | 0.2 | 200 | 0.0583 | 97.27 | 27.51 | 1.89 |

> **Bold** = best Transformer run.

---

## 4. Head-to-Head: Shared Metrics Only

The only metric reported by **all three** architectures is **Top-1 / Hit@1 accuracy**. Using each model's best run:

| Architecture | Best Run | Top-1 / Hit@1 Accuracy |
|-------------|----------|------------------------|
| **Transformer** | 20260227_002159 | **97.36%** |
| **GRU** | 20260213_025555 | **70.81%** |
| **LSTM** | Stage 3 (Regularized) | **27.1%** |

**Winner: Transformer** — leads GRU by +26.55 percentage points and LSTM by +70.26 percentage points.

---

## 5. Pairwise Comparisons (Shared Metrics Between Pairs)

### GRU vs LSTM (shared: Top-1, Top-5)

| Metric | Best GRU | Best LSTM | Winner |
|--------|----------|-----------|--------|
| **Top-1 / Hit@1** | 70.81% | 27.1% *(Stage 3)* | **GRU** (+43.7 pp) |
| **Top-5 / Hit@5** | 85.34% | 90.0% *(Stage 2)* | **LSTM** (+4.7 pp) |

### LSTM vs Transformer (shared: Top-1, Precision)

| Metric | Best LSTM | Best Transformer | Winner |
|--------|-----------|------------------|--------|
| **Top-1 / Hit@1** | 27.1% *(Stage 3)* | 97.36% | **Transformer** (+70.3 pp) |
| **Precision** | 50.0% *(Stage 3)* | 36.17% | **LSTM** (+13.8 pp) |

### GRU vs Transformer (shared: Top-1)

| Metric | Best GRU | Best Transformer | Winner |
|--------|----------|------------------|--------|
| **Top-1 / Hit@1** | 70.81% | 97.36% | **Transformer** (+26.5 pp) |

---

## 6. Summary

| Rank | Architecture | Top-1 Accuracy | Key Advantage |
|------|-------------|----------------|---------------|
| 1 | **Transformer** | 97.36% | Highest Top-1 by a wide margin |
| 2 | **GRU** | 70.81% | Strong Top-1; best Top-5 vs Transformer (85.34%, not shared) |
| 3 | **LSTM** | 27.1% | Best Top-5 vs GRU (90%); best Precision vs Transformer (50%) |

### Overall Winner: **Transformer**

On the only universally shared metric (Top-1 accuracy), the Transformer dominates at **97.36%**. In pairwise comparisons, the LSTM shows strengths in Top-5 coverage (90%) and Precision (50%), while the GRU is the most balanced middle-ground performer.

> **Caveat:** These architectures were not tested under identical conditions (different vocabularies, loss functions, and output spaces). A fully fair comparison would require the same dataset, splits, and evaluation protocol.
