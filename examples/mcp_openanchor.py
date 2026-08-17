#!/usr/bin/env python
"""Example: OpenAnchor real semantic caching (MCP-tool-backed).

Demonstrates the actual public API — SemanticCache backed by a real
embedding model (Ollama if reachable, else a deterministic offline
fallback) and a real SQLite cache store — via the same handlers exposed
over MCP.
"""

import asyncio

from openanchor._mcp_connector import SemanticCache
from openanchor._mcp_tools import OpenAnchorMCPHandler


async def main():
    # Link a token-event store so `attribute_token_cost` can do real 6D
    # attribution too. Optional — omit `store=` if you only want caching.
    cache = SemanticCache(cache_db_path="example_cache.db")
    handler = OpenAnchorMCPHandler(cache)

    cached = await handler.cache_prompt_embedding(
        prompt="Summarize this quarterly earnings report for a retail investor.",
        response="Revenue up 12% YoY; margins flat; guidance raised for Q4.",
        model="gpt-4",
    )
    print(f"Cached prompt as {cached['cache_key']} (embedder: {cached['embedder']})")

    similar = await handler.find_cached_similar(
        query_prompt="Summarize this quarter's earnings for a retail investor.",
        similarity_threshold=0.5,
    )
    print(f"Found {similar['total_matches']} similar cached prompt(s):")
    for match in similar["matches"]:
        print(f"  - {match['cache_key']} (similarity={match['similarity']:.3f}): {match['response']}")

    stats = await handler.get_cache_statistics(include_breakdown=True)
    print(f"Cache statistics: {stats}")

    # Optional: expose these tools over MCP for use from Claude/other MCP
    # clients. Binds to loopback (127.0.0.1) by default; passing
    # host="0.0.0.0" is an explicit, deliberate opt-in for wider exposure.
    #
    #   mcp_url = cache.start_mcp_connector()
    #   print(f"OpenAnchor MCP running at {mcp_url}")
    #   try:
    #       while True:
    #           await asyncio.sleep(1)
    #   except KeyboardInterrupt:
    #       cache.stop_mcp_connector()


if __name__ == "__main__":
    asyncio.run(main())
