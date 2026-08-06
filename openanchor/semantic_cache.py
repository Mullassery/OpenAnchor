"""Semantic Caching for OpenAnchor - reduce duplicate token usage through intelligent query caching."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict


@dataclass
class CachedEntry:
    """A cached LLM request/response pair with semantic similarity metrics."""

    query_hash: str
    query_text: str
    response_text: str
    tokens_saved: int
    similarity_score: float  # 0.0-1.0
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600  # 1 hour default

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return datetime.utcnow() > self.last_accessed + timedelta(seconds=self.ttl_seconds)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "query_hash": self.query_hash,
            "query_text": self.query_text,
            "response_text": self.response_text,
            "tokens_saved": self.tokens_saved,
            "similarity_score": self.similarity_score,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "ttl_seconds": self.ttl_seconds,
        }


class SemanticCache:
    """Semantic cache for LLM queries - deduplicates similar requests to save tokens."""

    def __init__(self, max_entries: int = 1000, similarity_threshold: float = 0.85):
        """
        Initialize semantic cache.

        Args:
            max_entries: Maximum number of cached entries
            similarity_threshold: Minimum similarity (0-1) to consider a match
        """
        self.max_entries = max_entries
        self.similarity_threshold = similarity_threshold
        self.cache: Dict[str, CachedEntry] = {}
        self.access_log: List[Dict[str, Any]] = []
        self.hit_count = 0
        self.miss_count = 0

    def _compute_query_hash(self, query: str) -> str:
        """Compute hash of query for fast lookup."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]

    def _compute_similarity(self, query1: str, query2: str) -> float:
        """
        Compute semantic similarity between two queries.

        Phase 1: Simple token overlap
        Phase 2: Would use embeddings
        """
        tokens1 = set(query1.lower().split())
        tokens2 = set(query2.lower().split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def get(self, query: str) -> Optional[str]:
        """
        Try to get a cached response for a query.

        Returns:
            Cached response if found and similar, None otherwise
        """
        query_hash = self._compute_query_hash(query)

        # Check exact hash match first
        if query_hash in self.cache and not self.cache[query_hash].is_expired():
            entry = self.cache[query_hash]
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self.hit_count += 1
            self.access_log.append({
                "type": "hit_exact",
                "query_hash": query_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "similarity": 1.0,
            })
            return entry.response_text

        # Check semantic similarity
        best_match = None
        best_similarity = 0.0

        for entry in self.cache.values():
            if entry.is_expired():
                continue

            similarity = self._compute_similarity(query, entry.query_text)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry

        if best_match and best_similarity >= self.similarity_threshold:
            best_match.access_count += 1
            best_match.last_accessed = datetime.utcnow()
            self.hit_count += 1
            self.access_log.append({
                "type": "hit_semantic",
                "query_hash": best_match.query_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "similarity": best_similarity,
            })
            return best_match.response_text

        self.miss_count += 1
        return None

    def put(self, query: str, response: str, tokens_saved: int = 0, similarity_score: float = 1.0):
        """
        Cache a query-response pair.

        Args:
            query: Input query
            response: LLM response
            tokens_saved: Estimated tokens saved by cache hit
            similarity_score: How similar to original query (1.0 = exact)
        """
        query_hash = self._compute_query_hash(query)

        # Evict oldest entry if at capacity
        if len(self.cache) >= self.max_entries and query_hash not in self.cache:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)
            del self.cache[oldest_key]

        entry = CachedEntry(
            query_hash=query_hash,
            query_text=query,
            response_text=response,
            tokens_saved=tokens_saved,
            similarity_score=similarity_score,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

        self.cache[query_hash] = entry

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_queries = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_queries * 100) if total_queries > 0 else 0.0

        total_tokens_saved = sum(e.tokens_saved for e in self.cache.values())

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate_percent": hit_rate,
            "total_entries": len(self.cache),
            "max_entries": self.max_entries,
            "total_tokens_saved": total_tokens_saved,
            "avg_similarity": sum(e.similarity_score for e in self.cache.values()) / len(self.cache) if self.cache else 0.0,
            "most_accessed_query": self._get_most_accessed(),
        }

    def _get_most_accessed(self) -> Optional[str]:
        """Get the most frequently accessed query."""
        if not self.cache:
            return None
        return max(self.cache.values(), key=lambda e: e.access_count).query_text[:100]

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.access_log.clear()
        self.hit_count = 0
        self.miss_count = 0

    def cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.cache[key]


class CacheOptimizer:
    """Analyze cache performance and recommend optimizations."""

    def __init__(self, cache: SemanticCache):
        self.cache = cache

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations to improve cache hit rate."""
        recommendations = []
        stats = self.cache.get_stats()

        # Low hit rate
        if stats["hit_rate_percent"] < 20:
            recommendations.append({
                "type": "low_hit_rate",
                "severity": "high",
                "message": f"Cache hit rate is {stats['hit_rate_percent']:.1f}%. Consider lowering similarity threshold.",
                "action": "lower_similarity_threshold",
            })

        # Near capacity
        if stats["total_entries"] > stats["max_entries"] * 0.9:
            recommendations.append({
                "type": "near_capacity",
                "severity": "medium",
                "message": f"Cache is {stats['total_entries'] / stats['max_entries'] * 100:.1f}% full.",
                "action": "increase_max_entries",
            })

        # High similarity but low tokens saved
        avg_tokens = stats["total_tokens_saved"] / max(stats["total_entries"], 1)
        if avg_tokens < 10:
            recommendations.append({
                "type": "low_token_savings",
                "severity": "low",
                "message": f"Average tokens saved per entry: {avg_tokens:.1f}. Cache efficiency could improve.",
                "action": "review_query_patterns",
            })

        return recommendations
