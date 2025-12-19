import json
import time
import numpy as np
import sys
import os
from datetime import datetime
from typing import List, Dict

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, project_root)

from agents.graphRAG.pipeline.rag_pipeline import GraphRAGPipeline
from agents.graphRAG.retrieval.gemini_llm import GeminiLLM
from agents.ingestion.Load.neo4j_client import Neo4jClient



# ---------------- Metrics ---------------- #

def recall_at_k(predicted: List[str], relevant: List[str], k: int) -> float:
    predicted_k = predicted[:k]
    hits = sum(1 for item in relevant if item in predicted_k)
    return hits / len(relevant) if relevant else 0.0

def precision_at_k(predicted: List[str], relevant: List[str], k: int) -> float:
    predicted_k = predicted[:k]
    hits = sum(1 for item in predicted_k if item in relevant)
    return hits / k if k else 0.0

def mean_reciprocal_rank(predicted: List[str], relevant: List[str]) -> float:
    for idx, item in enumerate(predicted):
        if item in relevant:
            return 1.0 / (idx + 1)
    return 0.0

# ---------------- Benchmark Runner ---------------- #

class Benchmark:
    def __init__(self, pipeline: GraphRAGPipeline, test_file: str):
        self.pipeline = pipeline
        self.test_file = test_file
        with open(test_file, "r", encoding="utf-8") as f:
            self.test_cases = json.load(f)

    def run(self, top_k: int = 5, save_path: str = "agents/graphRAG/benchmarks/benchmark_results.json"):
        results = []
        total_latency = 0.0

        for case in self.test_cases:
            prompt = case["prompt"]
            relevant_answers = case["expected_answer"]
            if not isinstance(relevant_answers, list):
                relevant_answers = [relevant_answers]

            start_time = time.time()
            response = self.pipeline.run(prompt)
            latency = time.time() - start_time
            total_latency += latency

            # Extract predicted results
            predicted = []
            if response.get("records"):
                for record in response["records"]:
                    predicted.append(list(record.values())[0])
            elif response.get("llm_answer"):
                predicted = [response["llm_answer"]]

            # Compute metrics
            rec = recall_at_k(predicted, relevant_answers, top_k)
            prec = precision_at_k(predicted, relevant_answers, top_k)
            mrr = mean_reciprocal_rank(predicted, relevant_answers)

            results.append({
                "prompt": prompt,
                "predicted": predicted[:top_k],
                "relevant": relevant_answers,
                "recall@k": rec,
                "precision@k": prec,
                "mrr": mrr,
                "latency_sec": latency
            })

        # Aggregate metrics
        avg_recall = np.mean([r["recall@k"] for r in results])
        avg_precision = np.mean([r["precision@k"] for r in results])
        avg_mrr = np.mean([r["mrr"] for r in results])
        avg_latency = total_latency / len(results) if results else 0.0

        summary = {
            "avg_recall@k": avg_recall,
            "avg_precision@k": avg_precision,
            "avg_mrr": avg_mrr,
            "avg_latency_sec": avg_latency,
            "num_tests": len(results),
            "timestamp": datetime.now().isoformat()
        }

        # Save results to JSON
        history = {"summary": summary, "results": results}
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

        print(f"Benchmark results saved to {save_path}")
        return results, summary

# ---------------- Example Usage ---------------- #

if __name__ == "__main__":
    neo4j_client = Neo4jClient()
    llm = GeminiLLM()
    pipeline = GraphRAGPipeline(neo4j_client.driver, llm)

    benchmark = Benchmark(pipeline, "agents/graphRAG/tests/data/test_data.json")
    results, summary = benchmark.run(top_k=5)
    print("\n=== Summary Metrics ===")
    print(summary)
