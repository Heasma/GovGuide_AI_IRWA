"""
GovGuide AI — Retrieval Benchmark Evaluator

Evaluates information retrieval pipelines across the evaluation queries dataset.

Metrics:
- Precision@5: Proportion of top 5 retrieved items that match ground-truth service codes.
- Recall@5: Proportion of ground-truth service codes retrieved in top 5 items.
- MRR@10 (Mean Reciprocal Rank): Reciprocal rank of the first relevant service in top 10.
- Latency (ms): Mean, Median, and P95 execution latency.

Compares:
1. BM25 Lexical Retrieval
2. Semantic Vector Retrieval
3. Hybrid RRF Retrieval
"""

import json
import logging
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.retrieval.chunk_generator import generate_chunks_from_db
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.semantic_retriever import SemanticRetriever, LocalDeterministicEmbeddingProvider
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parents[3]
QUERIES_FILE = PROJECT_ROOT / "data" / "evaluation" / "retrieval_queries.json"
OUTPUT_REPORT = PROJECT_ROOT / "data" / "evaluation" / "retrieval_evaluation_report.json"


def calculate_metrics_for_query(
    retrieved_codes: List[str],
    expected_codes: List[str],
    k_precision: int = 5,
    k_mrr: int = 10,
) -> Tuple[float, float, float]:
    """
    Calculate Precision@k, Recall@k, and MRR@k for a single query.

    Returns:
        (precision_at_k, recall_at_k, mrr_at_k)
    """
    if not expected_codes:
        return 0.0, 0.0, 0.0

    expected_set = set(expected_codes)

    # Precision@K: fraction of retrieved top-K that are relevant
    top_k_retrieved = retrieved_codes[:k_precision]
    if top_k_retrieved:
        hits = sum(1 for code in top_k_retrieved if code in expected_set)
        p_at_k = hits / len(top_k_retrieved)
    else:
        p_at_k = 0.0

    # Recall@K: fraction of expected codes retrieved in top-K
    retrieved_in_k = set(top_k_retrieved)
    found_expected = expected_set.intersection(retrieved_in_k)
    r_at_k = len(found_expected) / len(expected_set)

    # MRR@10: 1 / rank of first relevant item in top 10 (1-indexed)
    mrr = 0.0
    for rank, code in enumerate(retrieved_codes[:k_mrr], start=1):
        if code in expected_set:
            mrr = 1.0 / rank
            break

    return p_at_k, r_at_k, mrr


class RetrievalEvaluator:
    """
    Benchmark evaluator for the retrieval layer.
    """

    def __init__(self, queries_path: Optional[Path] = None):
        self.queries_path = queries_path or QUERIES_FILE
        self.queries: List[Dict[str, Any]] = []
        self._load_queries()

    def _load_queries(self) -> None:
        if not self.queries_path.exists():
            raise FileNotFoundError(f"Queries file not found: {self.queries_path}")
        with open(self.queries_path, "r", encoding="utf-8") as f:
            self.queries = json.load(f)

    def evaluate(self, service: Optional[RetrievalService] = None) -> Dict[str, Any]:
        """
        Run benchmark across all evaluation queries for BM25, Semantic, and Hybrid modes.
        """
        if service is None:
            service = RetrievalService()

        modes = ["bm25", "semantic", "hybrid"]
        results_by_mode: Dict[str, Any] = {}

        for mode in modes:
            precisions: List[float] = []
            recalls: List[float] = []
            mrrs: List[float] = []
            latencies_ms: List[float] = []
            query_details: List[Dict[str, Any]] = []

            for q_item in self.queries:
                qid = q_item["id"]
                query_text = q_item["query"]
                expected = q_item.get("expected_service_codes", [])

                start_t = time.perf_counter()
                bundle = service.search(query=query_text, top_k=10, mode=mode)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                latencies_ms.append(elapsed_ms)

                retrieved_codes = [r.service_code for r in bundle.results if r.service_code]

                p5, r5, mrr10 = calculate_metrics_for_query(
                    retrieved_codes, expected, k_precision=5, k_mrr=10
                )
                precisions.append(p5)
                recalls.append(r5)
                mrrs.append(mrr10)

                query_details.append({
                    "query_id": qid,
                    "query": query_text,
                    "expected": expected,
                    "retrieved_top5": retrieved_codes[:5],
                    "precision_at_5": round(p5, 4),
                    "recall_at_5": round(r5, 4),
                    "mrr_at_10": round(mrr10, 4),
                    "latency_ms": round(elapsed_ms, 2),
                })

            avg_p5 = statistics.mean(precisions) if precisions else 0.0
            avg_r5 = statistics.mean(recalls) if recalls else 0.0
            avg_mrr = statistics.mean(mrrs) if mrrs else 0.0
            avg_lat = statistics.mean(latencies_ms) if latencies_ms else 0.0
            med_lat = statistics.median(latencies_ms) if latencies_ms else 0.0
            p95_lat = statistics.quantiles(latencies_ms, n=20)[18] if len(latencies_ms) >= 20 else max(latencies_ms, default=0.0)

            results_by_mode[mode] = {
                "precision_at_5": round(avg_p5, 4),
                "recall_at_5": round(avg_r5, 4),
                "mrr_at_10": round(avg_mrr, 4),
                "latency_avg_ms": round(avg_lat, 2),
                "latency_median_ms": round(med_lat, 2),
                "latency_p95_ms": round(p95_lat, 2),
                "queries_evaluated": len(self.queries),
                "query_results": query_details,
            }

        report = {
            "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_queries": len(self.queries),
            "modes": results_by_mode,
            "summary": {
                "best_mrr_mode": max(modes, key=lambda m: results_by_mode[m]["mrr_at_10"]),
                "best_recall_mode": max(modes, key=lambda m: results_by_mode[m]["recall_at_5"]),
                "hybrid_precision_at_5": results_by_mode["hybrid"]["precision_at_5"],
                "hybrid_recall_at_5": results_by_mode["hybrid"]["recall_at_5"],
                "hybrid_mrr_at_10": results_by_mode["hybrid"]["mrr_at_10"],
                "hybrid_latency_avg_ms": results_by_mode["hybrid"]["latency_avg_ms"],
                "hybrid_latency_p95_ms": results_by_mode["hybrid"]["latency_p95_ms"],
            }
        }

        OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info("Retrieval evaluation report saved to %s", OUTPUT_REPORT)

        return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    evaluator = RetrievalEvaluator()
    rep = evaluator.evaluate()
    print("\n=== RETRIEVAL EVALUATION REPORT ===")
    print(f"Total Queries: {rep['total_queries']}")
    for mode_name, data in rep["modes"].items():
        print(f"\n[{mode_name.upper()}]")
        print(f"  Precision@5 : {data['precision_at_5']:.4f}")
        print(f"  Recall@5    : {data['recall_at_5']:.4f}")
        print(f"  MRR@10      : {data['mrr_at_10']:.4f}")
        print(f"  Latency Avg : {data['latency_avg_ms']:.2f} ms")
        print(f"  Latency P95 : {data['latency_p95_ms']:.2f} ms")
