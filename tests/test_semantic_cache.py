"""Tests for semantic caching."""

import pytest
from openanchor.semantic_cache import SemanticCache, CacheOptimizer


class TestSemanticCache:
    """Test semantic cache functionality."""

    def test_cache_initialization(self):
        """Test cache creation."""
        cache = SemanticCache(max_entries=100)
        assert cache.max_entries == 100
        assert cache.hit_count == 0
        assert cache.miss_count == 0

    def test_exact_match_retrieval(self):
        """Test exact query matching."""
        cache = SemanticCache()
        query = "What is the meaning of life?"
        response = "42"

        cache.put(query, response)
        retrieved = cache.get(query)

        assert retrieved == response
        assert cache.hit_count == 1

    def test_semantic_similarity_matching(self):
        """Test semantic similarity matching."""
        cache = SemanticCache(similarity_threshold=0.3)  # Lower threshold for simple token overlap

        query1 = "What is artificial intelligence and machine learning?"
        response1 = "AI is the simulation of human intelligence."

        cache.put(query1, response1, tokens_saved=50)

        # Similar query should match
        query2 = "Explain artificial intelligence and machine learning"
        retrieved = cache.get(query2)

        assert retrieved is not None

    def test_cache_miss(self):
        """Test cache miss when no similar query."""
        cache = SemanticCache(similarity_threshold=0.9)
        cache.put("How is weather?", "Sunny")

        retrieved = cache.get("Tell me a joke")
        assert retrieved is None
        assert cache.miss_count == 1

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = SemanticCache()
        cache.put("Query 1", "Response 1", tokens_saved=100)
        cache.put("Query 2", "Response 2", tokens_saved=50)

        cache.get("Query 1")
        cache.get("Unknown")

        stats = cache.get_stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["total_entries"] == 2
        assert stats["total_tokens_saved"] == 150

    def test_cache_expiration(self):
        """Test cache entry expiration."""
        cache = SemanticCache()
        query = "Test query"
        response = "Test response"

        cache.put(query, response)
        assert cache.get(query) is not None

        # Manually expire the entry
        for entry in cache.cache.values():
            entry.ttl_seconds = 0  # Immediately expire

        assert cache.get(query) is None
        assert cache.miss_count == 1

    def test_cache_overflow(self):
        """Test cache eviction at capacity."""
        cache = SemanticCache(max_entries=3)

        # Fill cache
        for i in range(3):
            cache.put(f"Query {i}", f"Response {i}")

        assert len(cache.cache) == 3

        # Add one more - should evict oldest
        cache.put("Query 3", "Response 3")
        assert len(cache.cache) == 3

    def test_access_logging(self):
        """Test access logging."""
        cache = SemanticCache()
        cache.put("Test", "Response")
        cache.get("Test")

        assert len(cache.access_log) > 0
        assert cache.access_log[0]["type"] == "hit_exact"


class TestCacheOptimizer:
    """Test cache optimization recommendations."""

    def test_low_hit_rate_recommendation(self):
        """Test recommendation for low hit rate."""
        cache = SemanticCache(similarity_threshold=0.99)  # High threshold = low hits

        # Create cache with many queries
        for i in range(20):
            cache.put(f"Query {i}", f"Response {i}")

        # Try to get different queries
        for i in range(20, 40):
            cache.get(f"Query {i}")

        optimizer = CacheOptimizer(cache)
        recommendations = optimizer.get_optimization_recommendations()

        # Should have low hit rate recommendation
        assert any(r["type"] == "low_hit_rate" for r in recommendations)

    def test_near_capacity_recommendation(self):
        """Test recommendation when cache near full."""
        cache = SemanticCache(max_entries=5)

        # Fill cache to 90% capacity
        for i in range(5):
            cache.put(f"Query {i}", f"Response {i}")

        optimizer = CacheOptimizer(cache)
        recommendations = optimizer.get_optimization_recommendations()

        # Should have capacity warning
        assert any(r["type"] == "near_capacity" for r in recommendations)
