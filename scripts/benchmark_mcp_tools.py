#!/usr/bin/env python3
"""Latency/throughput benchmark for OpenAnchor MCP-backed cache tools.

Stdlib only. Uses a temporary SQLite cache and the deterministic offline
embedder so results are reproducible and need no network.

    python scripts/benchmark_mcp_tools.py --count 200
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import tempfile
import time
from pathlib import Path

from openanchor._mcp_connector import SemanticCache
from openanchor._mcp_tools import OpenAnchorMCPHandler
from openanchor.semantic_cache import HashingEmbeddingProvider


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


async def run(count: int, dim: int) -> None:
    with tempfile.TemporaryDirectory(prefix="openanchor-bench-") as directory:
        cache = SemanticCache(
            cache_db_path=str(Path(directory) / "cache.db"),
            embedder=HashingEmbeddingProvider(dim=dim),
        )
        handler = OpenAnchorMCPHandler(cache)
        try:
            write_latencies: list[float] = []
            for index in range(count):
                prompt = f"Summarize support ticket {index} about billing question {index}"
                started = time.perf_counter()
                await handler.cache_prompt_embedding(prompt, response=f"reply {index}")
                write_latencies.append((time.perf_counter() - started) * 1000)

            lookup_latencies: list[float] = []
            matches = 0
            started_batch = time.perf_counter()
            for index in range(count):
                prompt = f"Summarize support ticket {index} about billing question {index}"
                started = time.perf_counter()
                result = await handler.find_cached_similar(
                    prompt, similarity_threshold=0.5, limit=5
                )
                lookup_latencies.append((time.perf_counter() - started) * 1000)
                matches += result["total_matches"]
            batch_seconds = time.perf_counter() - started_batch

            print(f"entries: {count}  embedder_dim: {dim}")
            print(
                "cache write ms: "
                f"mean={statistics.fmean(write_latencies):.2f} "
                f"p50={percentile(write_latencies, 0.5):.2f} "
                f"p95={percentile(write_latencies, 0.95):.2f}"
            )
            print(
                "cache lookup ms: "
                f"mean={statistics.fmean(lookup_latencies):.2f} "
                f"p50={percentile(lookup_latencies, 0.5):.2f} "
                f"p95={percentile(lookup_latencies, 0.95):.2f}"
            )
            print(f"lookup throughput: {count / batch_seconds:.1f} lookups/sec")
            print(f"total matches observed: {matches}")
        finally:
            cache.cache.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=200, help="Entries/lookups")
    parser.add_argument("--dim", type=int, default=128, help="Embedding dimension")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    asyncio.run(run(args.count, args.dim))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
