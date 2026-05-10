# evaluation/evaluate_retrieval.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.ground_truth_corrected import TEST_QUERIES
from app.services.retrieval import search_assessments
from evaluation.evaluation_metrics import EvaluationMetricsCalculator

print("=" * 70)
print("RETRIEVAL QUALITY EVALUATION")
print("=" * 70)

calculator = EvaluationMetricsCalculator()
total_recall = 0
count = 0

for test in TEST_QUERIES:
    if test.get('relevant_assessments'):
        query = test['query']
        relevant = test['relevant_assessments']
        
        results = search_assessments(query, k=10, return_type="metadata")
        retrieved = [r.get('name', '') for r in results]
        
        metrics = calculator.compute_retrieval_metrics(retrieved, relevant)
        recall = metrics.recall_at_k.get(10, 0)
        total_recall += recall
        count += 1
        
        print(f"\nQuery: {query}")
        print(f"  Recall@10: {recall:.3f}")
        print(f"  Precision@5: {metrics.precision_at_k.get(5, 0):.3f}")
        print(f"  MRR: {metrics.mrr:.3f}")

print(f"\n📊 Mean Recall@10: {total_recall/count:.3f}" if count else "No tests with ground truth")
