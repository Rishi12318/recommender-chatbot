# evaluation/evaluation_metrics.py
"""
Comprehensive evaluation metrics for retrieval quality, recommendation relevance, 
groundedness, and overall response accuracy.
"""

import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval quality"""
    precision_at_k: Dict[int, float] = field(default_factory=dict)  # P@1, P@5, P@10
    recall_at_k: Dict[int, float] = field(default_factory=dict)
    ndcg_at_k: Dict[int, float] = field(default_factory=dict)  # Normalized DCG
    mrr: float = 0.0  # Mean Reciprocal Rank
    map_score: float = 0.0  # Mean Average Precision


@dataclass
class RecommendationMetrics:
    """Metrics for recommendation relevance"""
    relevance_score: float = 0.0  # 0-1, how well recs match query
    diversity_score: float = 0.0  # 0-1, how diverse the recommendations are
    coverage_score: float = 0.0  # 0-1, how many relevant assessments were covered
    ranking_quality: float = 0.0  # 0-1, are best matches ranked highest


@dataclass
class GroundednessMetrics:
    """Metrics for verifying recommendations are grounded in catalog"""
    all_exist_in_catalog: bool = True
    all_have_metadata: bool = True
    missing_references: List[str] = field(default_factory=list)
    groundedness_score: float = 0.0  # 0-1


@dataclass
class ResponseAccuracyMetrics:
    """Metrics for overall response accuracy and effectiveness"""
    on_topic_accuracy: float = 0.0  # Is response on-topic?
    query_understanding: float = 0.0  # Did agent understand the query?
    completeness: float = 0.0  # Did agent address all requirements?
    clarity: float = 0.0  # Is the response clear and actionable?
    overall_effectiveness: float = 0.0  # 0-1


class EvaluationMetricsCalculator:
    """Calculate comprehensive evaluation metrics"""
    
    def __init__(self, catalog_path: str = None):
        self.catalog_path = Path(catalog_path) if catalog_path else Path("app/data/processed_catalog.json")
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> List[Dict]:
        """Load assessment catalog"""
        if self.catalog_path.exists():
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    # ============= RETRIEVAL QUALITY METRICS =============
    
    def calculate_precision_at_k(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        """Precision@K: Of the top-K retrieved items, how many are relevant?"""
        if k == 0 or not retrieved:
            return 0.0
        top_k = retrieved[:k]
        matches = len(set(top_k) & set(relevant))
        return matches / k
    
    def calculate_recall_at_k(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        """Recall@K: Of all relevant items, how many were in top-K?"""
        if len(relevant) == 0:
            return 0.0
        top_k = retrieved[:k]
        matches = len(set(top_k) & set(relevant))
        return matches / len(relevant)
    
    def calculate_ndcg_at_k(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        """Normalized Discounted Cumulative Gain@K"""
        def dcg(rankings, k_val):
            score = 0.0
            for i in range(min(k_val, len(rankings))):
                is_relevant = 1.0 if rankings[i] in relevant else 0.0
                score += is_relevant / (i + 1)  # Simplified discount
            return score
        
        if not retrieved:
            return 0.0
        
        top_k = retrieved[:k]
        actual_dcg = dcg(top_k, k)
        
        # iDCG = all relevant items first
        ideal_ranking = relevant[:k] + [x for x in retrieved if x not in relevant[:k]][:k - len(relevant)]
        ideal_dcg = dcg(ideal_ranking, k)
        
        if ideal_dcg == 0:
            return 0.0
        return actual_dcg / ideal_dcg
    
    def calculate_mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        """Mean Reciprocal Rank: 1 / rank of first relevant result"""
        for i, item in enumerate(retrieved):
            if item in relevant:
                return 1.0 / (i + 1)
        return 0.0
    
    def calculate_map(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        """Mean Average Precision"""
        if len(relevant) == 0 or not retrieved:
            return 0.0
        
        score = 0.0
        num_hits = 0
        for i in range(min(k, len(retrieved))):
            if retrieved[i] in relevant:
                num_hits += 1
                score += num_hits / (i + 1)
        
        return score / len(relevant)
    
    def compute_retrieval_metrics(self, retrieved: List[str], relevant: List[str]) -> RetrievalMetrics:
        """Compute all retrieval metrics"""
        metrics = RetrievalMetrics()
        
        for k in [1, 5, 10]:
            metrics.precision_at_k[k] = self.calculate_precision_at_k(retrieved, relevant, k)
            metrics.recall_at_k[k] = self.calculate_recall_at_k(retrieved, relevant, k)
            metrics.ndcg_at_k[k] = self.calculate_ndcg_at_k(retrieved, relevant, k)
        
        metrics.mrr = self.calculate_mrr(retrieved, relevant)
        metrics.map_score = self.calculate_map(retrieved, relevant)
        
        return metrics
    
    # ============= RECOMMENDATION RELEVANCE METRICS =============
    
    def calculate_relevance_score(self, recommendations: List[Dict], query: str) -> float:
        """Score how well recommendations match the query"""
        query_lower = query.lower()
        if not recommendations:
            return 0.0
        
        query_keywords = set(query_lower.split())
        if not query_keywords:
            return 0.5
        
        total_score = 0.0
        for rec in recommendations[:10]:
            rec_text = (rec.get('name', '') + ' ' + rec.get('description', '')).lower()
            matches = sum(1 for kw in query_keywords if kw in rec_text)
            total_score += min(matches / len(query_keywords), 1.0)
        
        return total_score / max(len(recommendations[:10]), 1)
    
    def calculate_diversity_score(self, recommendations: List[Dict]) -> float:
        """Score the diversity of recommendations"""
        if len(recommendations) < 2:
            return 0.0
        
        test_types = set()
        job_levels = set()
        
        for rec in recommendations:
            test_types.update(rec.get('test_types', []))
            job_levels.update(rec.get('job_levels', []))
        
        type_score = min(len(test_types) / 3.0, 1.0) if test_types else 0.5
        level_score = min(len(job_levels) / 3.0, 1.0) if job_levels else 0.5
        
        return (type_score + level_score) / 2.0
    
    def calculate_coverage_score(self, recommendations: List[Dict], all_relevant: List[str]) -> float:
        """What % of relevant assessments were recommended?"""
        if not all_relevant:
            return 1.0
        
        rec_names = {r.get('name', '').lower().strip() for r in recommendations}
        relevant_lower = {r.lower().strip() for r in all_relevant}
        
        if not relevant_lower:
            return 1.0
        
        matches = len(rec_names & relevant_lower)
        return matches / len(relevant_lower)
    
    def compute_recommendation_metrics(self, recommendations: List[Dict], query: str, 
                                     relevant_assessments: List[str]) -> RecommendationMetrics:
        """Compute all recommendation metrics"""
        metrics = RecommendationMetrics()
        metrics.relevance_score = self.calculate_relevance_score(recommendations, query)
        metrics.diversity_score = self.calculate_diversity_score(recommendations)
        metrics.coverage_score = self.calculate_coverage_score(recommendations, relevant_assessments)
        metrics.ranking_quality = metrics.relevance_score
        
        return metrics
    
    # ============= GROUNDEDNESS METRICS =============
    
    def calculate_groundedness(self, recommendations: List[Dict]) -> GroundednessMetrics:
        """Verify that all recommendations exist in the catalog"""
        metrics = GroundednessMetrics()
        
        if not recommendations:
            metrics.groundedness_score = 1.0
            return metrics
        
        catalog_names = {r.get('name', '').lower().strip() for r in self.catalog}
        missing = []
        
        for rec in recommendations:
            name = rec.get('name', '').lower().strip()
            if name and name not in catalog_names:
                missing.append(rec.get('name', 'Unknown'))
                metrics.all_exist_in_catalog = False
            
            if not rec.get('test_types') or not rec.get('url'):
                metrics.all_have_metadata = False
        
        metrics.missing_references = missing
        metrics.groundedness_score = max(0.0, 1.0 - (len(missing) / max(len(recommendations), 1)))
        
        return metrics
    
    # ============= RESPONSE ACCURACY METRICS =============
    
    def calculate_response_accuracy(self, response: str, query: str, recommendations: List[Dict],
                                   expected_behavior: str = "recommend") -> ResponseAccuracyMetrics:
        """Measure overall response accuracy"""
        metrics = ResponseAccuracyMetrics()
        
        response_lower = response.lower()
        query_lower = query.lower()
        
        # On-topic accuracy
        off_topic_words = ["weather", "sports", "movie", "recipe", "game", "song"]
        on_topic_words = ["assess", "test", "hire", "skill", "role", "candidate", "shl"]
        
        has_off_topic = any(w in response_lower for w in off_topic_words)
        has_on_topic = any(w in response_lower for w in on_topic_words)
        metrics.on_topic_accuracy = 1.0 if (has_on_topic and not has_off_topic) else (0.5 if has_on_topic else 0.0)
        
        # Query understanding
        query_keywords = [w for w in query_lower.split() if len(w) > 3]
        if query_keywords:
            matched_keywords = sum(1 for kw in query_keywords if kw in response_lower)
            metrics.query_understanding = matched_keywords / len(query_keywords)
        else:
            metrics.query_understanding = 0.5
        
        # Completeness
        if expected_behavior == "recommend":
            metrics.completeness = 1.0 if len(recommendations) > 0 else 0.0
        elif expected_behavior == "ask":
            metrics.completeness = 1.0 if "?" in response else 0.0
        else:
            metrics.completeness = 0.5
        
        # Clarity
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if sentences:
            avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
            metrics.clarity = 1.0 if 5 <= avg_words <= 25 else 0.7
        else:
            metrics.clarity = 0.5
        
        # Overall effectiveness
        metrics.overall_effectiveness = sum([
            metrics.on_topic_accuracy * 0.3,
            metrics.query_understanding * 0.25,
            metrics.completeness * 0.25,
            metrics.clarity * 0.2
        ])
        
        return metrics