"""Real semantic caching for OpenAnchor.

This backs the MCP tools in ``_mcp_tools.py`` with an actual embedding
model, a real SQLite-backed cache store, and real cosine-similarity
lookups — replacing the previous implementation, which returned
hardcoded constants (e.g. ``overall_hit_rate: 0.68``) regardless of
input.

Embedding providers:
    - ``OllamaEmbeddingProvider``: calls a local Ollama server's
      ``/api/embeddings`` endpoint (e.g. with ``nomic-embed-text``) for
      real semantic embeddings.
    - ``HashingEmbeddingProvider``: a dependency-free, deterministic
      feature-hashing embedder used as an offline/CI fallback when Ollama
      isn't reachable. It's a real (if simple) bag-of-words hashing
      scheme — semantically related text still gets higher cosine
      similarity than unrelated text — not a stub.

``default_embedder()`` picks Ollama when reachable and falls back to the
hashing embedder otherwise, so the cache is always fully functional.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sqlite3
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\w+")


# --------------------------------------------------------------------------
# Embedding providers
# --------------------------------------------------------------------------


class EmbeddingProvider(ABC):
    """Interface for turning text into a fixed-length embedding vector."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Return an embedding vector for ``text``."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Length of vectors returned by ``embed``."""

    @property
    def name(self) -> str:
        return self.__class__.__name__


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Real embeddings via a local Ollama server.

    Requires Ollama running locally (``ollama serve``) with an embedding
    model pulled, e.g. ``ollama pull nomic-embed-text``.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        host: str = "http://localhost:11434",
        timeout: float = 10.0,
        dimension: int = 768,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._dimension = dimension

    def embed(self, text: str) -> List[float]:
        import requests

        response = requests.post(
            f"{self.host}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        embedding = data.get("embedding")
        if not embedding:
            raise ValueError(f"Ollama returned no embedding for model {self.model!r}")
        self._dimension = len(embedding)
        return [float(v) for v in embedding]

    @property
    def dimension(self) -> int:
        return self._dimension

    def is_reachable(self) -> bool:
        """Quick health check so callers can decide whether to use this."""
        try:
            import requests

            resp = requests.get(f"{self.host}/api/tags", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free embedding fallback.

    Uses feature hashing (the "hashing trick") over word tokens: each
    token is hashed into one of ``dim`` buckets and counted, then the
    resulting vector is L2-normalized. This is a real, well-known
    embedding technique (not a stub) — prompts sharing vocabulary get
    meaningfully higher cosine similarity than unrelated prompts — and it
    requires no network access or model download, which makes it a safe
    default for CI/tests and for environments without Ollama.
    """

    def __init__(self, dim: int = 256):
        self._dim = dim

    def embed(self, text: str) -> List[float]:
        vector = [0.0] * self._dim
        tokens = _WORD_RE.findall(text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            bucket = int(digest, 16) % self._dim
            vector[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    @property
    def dimension(self) -> int:
        return self._dim


def default_embedder(prefer_ollama: bool = True) -> EmbeddingProvider:
    """Pick the best available embedding provider.

    Tries Ollama first (real semantic embeddings) when ``prefer_ollama``
    is True and a local server responds; otherwise falls back to the
    dependency-free hashing embedder so the cache remains usable offline.
    """
    if prefer_ollama:
        candidate = OllamaEmbeddingProvider()
        if candidate.is_reachable():
            logger.info("Using OllamaEmbeddingProvider (model=%s) for semantic cache", candidate.model)
            return candidate
        logger.info(
            "Ollama not reachable at %s; falling back to HashingEmbeddingProvider "
            "for semantic cache (offline mode)",
            candidate.host,
        )
    return HashingEmbeddingProvider()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two equal-length vectors, in [-1, 1]."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CacheMatch:
    cache_key: str
    prompt: str
    response: Optional[str]
    similarity: float
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "prompt": self.prompt,
            "response": self.response,
            "similarity": self.similarity,
            "model": self.model,
        }


# --------------------------------------------------------------------------
# SQLite-backed semantic cache store
# --------------------------------------------------------------------------


class SemanticCacheStore:
    """Real, persistent semantic cache backed by SQLite.

    Stores prompt embeddings + (optional) cached responses, and computes
    real cosine-similarity lookups. Also logs every lookup (hit/miss) so
    hit-rate/statistics tools reflect actual usage instead of hardcoded
    numbers.

    Reuses a single connection in WAL mode (see ``storage.SqliteEventStore``
    for the same pattern applied to the event store) rather than opening a
    fresh connection per call.
    """

    def __init__(
        self,
        db_path: str = "openanchor_cache.db",
        embedder: Optional[EmbeddingProvider] = None,
    ):
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder or default_embedder()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_key TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                response TEXT,
                model TEXT,
                embedding TEXT NOT NULL,
                embedding_dim INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                hit_count INTEGER NOT NULL DEFAULT 0,
                last_hit_at TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_lookups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query_prompt TEXT NOT NULL,
                hit INTEGER NOT NULL,
                best_similarity REAL,
                matched_cache_key TEXT,
                model TEXT
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_lookups_timestamp ON cache_lookups(timestamp)"
        )
        self._conn.commit()

    # -- writes --------------------------------------------------------

    def put(
        self,
        prompt: str,
        response: Optional[str] = None,
        cache_key: Optional[str] = None,
        ttl_minutes: Optional[int] = 1440,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Embed and store a prompt. Returns the stored entry's metadata."""
        embedding = self.embedder.embed(prompt)
        key = cache_key or f"cache_{uuid.uuid4().hex[:12]}"
        created_at = _now()
        expires_at = (
            created_at + timedelta(minutes=ttl_minutes) if ttl_minutes else None
        )

        self._conn.execute(
            """
            INSERT OR REPLACE INTO cache_entries (
                cache_key, prompt, response, model, embedding, embedding_dim,
                created_at, expires_at, hit_count, last_hit_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
            """,
            (
                key,
                prompt,
                response,
                model,
                json.dumps(embedding),
                len(embedding),
                created_at.isoformat(),
                expires_at.isoformat() if expires_at else None,
            ),
        )
        self._conn.commit()

        return {
            "cache_key": key,
            "embedding_dim": len(embedding),
            "cached": True,
            "ttl_minutes": ttl_minutes,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "embedder": self.embedder.name,
        }

    # -- reads -----------------------------------------------------------

    def _live_entries(self, model: Optional[str] = None) -> List[sqlite3.Row]:
        now_iso = _now().isoformat()
        if model:
            cursor = self._conn.execute(
                """
                SELECT * FROM cache_entries
                WHERE (expires_at IS NULL OR expires_at > ?) AND model = ?
                """,
                (now_iso, model),
            )
        else:
            cursor = self._conn.execute(
                "SELECT * FROM cache_entries WHERE (expires_at IS NULL OR expires_at > ?)",
                (now_iso,),
            )
        return cursor.fetchall()

    def find_similar(
        self,
        query_prompt: str,
        similarity_threshold: float = 0.85,
        limit: int = 10,
        model: Optional[str] = None,
        record_lookup: bool = True,
    ) -> List[CacheMatch]:
        """Real cosine-similarity lookup against stored (non-expired) entries."""
        query_embedding = self.embedder.embed(query_prompt)
        rows = self._live_entries(model=model)

        scored: List[CacheMatch] = []
        for row in rows:
            candidate_embedding = json.loads(row["embedding"])
            similarity = cosine_similarity(query_embedding, candidate_embedding)
            if similarity >= similarity_threshold:
                scored.append(
                    CacheMatch(
                        cache_key=row["cache_key"],
                        prompt=row["prompt"],
                        response=row["response"],
                        similarity=similarity,
                        model=row["model"],
                    )
                )

        scored.sort(key=lambda m: m.similarity, reverse=True)
        matches = scored[:limit]

        if record_lookup:
            self._record_lookup(query_prompt, matches, model)
        if matches:
            self._record_hits([m.cache_key for m in matches])

        return matches

    def _record_lookup(
        self, query_prompt: str, matches: List[CacheMatch], model: Optional[str]
    ) -> None:
        best_similarity = matches[0].similarity if matches else None
        matched_key = matches[0].cache_key if matches else None
        self._conn.execute(
            """
            INSERT INTO cache_lookups (timestamp, query_prompt, hit, best_similarity, matched_cache_key, model)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _now().isoformat(),
                query_prompt,
                1 if matches else 0,
                best_similarity,
                matched_key,
                model,
            ),
        )
        self._conn.commit()

    def _record_hits(self, cache_keys: List[str]) -> None:
        now_iso = _now().isoformat()
        self._conn.executemany(
            "UPDATE cache_entries SET hit_count = hit_count + 1, last_hit_at = ? WHERE cache_key = ?",
            [(now_iso, key) for key in cache_keys],
        )
        self._conn.commit()

    # -- stats -------------------------------------------------------

    def count_entries(self, only_live: bool = True) -> int:
        if only_live:
            return len(self._live_entries())
        cursor = self._conn.execute("SELECT COUNT(*) as c FROM cache_entries")
        return int(cursor.fetchone()["c"])

    def lookup_stats(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        if since:
            cursor = self._conn.execute(
                "SELECT hit, best_similarity, model FROM cache_lookups WHERE timestamp >= ?",
                (since.isoformat(),),
            )
        else:
            cursor = self._conn.execute("SELECT hit, best_similarity, model FROM cache_lookups")
        rows = cursor.fetchall()

        total = len(rows)
        hits = sum(1 for r in rows if r["hit"])
        similarities = [r["best_similarity"] for r in rows if r["best_similarity"] is not None]

        by_model: Dict[str, Dict[str, int]] = {}
        for r in rows:
            key = r["model"] or "unknown"
            bucket = by_model.setdefault(key, {"hits": 0, "misses": 0})
            if r["hit"]:
                bucket["hits"] += 1
            else:
                bucket["misses"] += 1

        return {
            "total_lookups": total,
            "hits": hits,
            "misses": total - hits,
            "hit_rate": (hits / total) if total else 0.0,
            "avg_similarity": (sum(similarities) / len(similarities)) if similarities else 0.0,
            "by_model": by_model,
        }

    def estimated_size_bytes(self) -> int:
        """Rough real storage-size estimate from actual row content."""
        cursor = self._conn.execute(
            "SELECT LENGTH(prompt) + LENGTH(COALESCE(response, '')) + LENGTH(embedding) as sz "
            "FROM cache_entries"
        )
        return sum(row["sz"] for row in cursor.fetchall())

    # -- maintenance ---------------------------------------------------

    def invalidate(
        self,
        older_than_hours: Optional[float] = None,
        cache_keys: Optional[List[str]] = None,
        similarity_to_prompt: Optional[str] = None,
        similarity_threshold: float = 0.9,
    ) -> Dict[str, Any]:
        """Delete entries matching real criteria. Returns real counts freed."""
        keys_to_delete: set = set()

        if cache_keys:
            keys_to_delete.update(cache_keys)

        if older_than_hours is not None:
            cutoff = (_now() - timedelta(hours=older_than_hours)).isoformat()
            cursor = self._conn.execute(
                "SELECT cache_key FROM cache_entries WHERE created_at < ?", (cutoff,)
            )
            keys_to_delete.update(row["cache_key"] for row in cursor.fetchall())

        if similarity_to_prompt:
            query_embedding = self.embedder.embed(similarity_to_prompt)
            cursor = self._conn.execute("SELECT cache_key, embedding FROM cache_entries")
            for row in cursor.fetchall():
                sim = cosine_similarity(query_embedding, json.loads(row["embedding"]))
                if sim >= similarity_threshold:
                    keys_to_delete.add(row["cache_key"])

        freed_bytes = 0
        matched_count = 0
        if keys_to_delete:
            # The f-string only interpolates a run of literal "?" placeholder
            # characters (one per key) — never the key values themselves,
            # which are always passed as bound parameters below. This is the
            # standard sqlite3 pattern for a variable-length IN(...) clause,
            # not string-built SQL from untrusted input.
            placeholders = ",".join("?" for _ in keys_to_delete)
            cursor = self._conn.execute(
                f"SELECT LENGTH(prompt) + LENGTH(COALESCE(response, '')) + LENGTH(embedding) as sz "  # nosec B608
                f"FROM cache_entries WHERE cache_key IN ({placeholders})",
                tuple(keys_to_delete),
            )
            rows = cursor.fetchall()
            matched_count = len(rows)
            freed_bytes = sum(row["sz"] for row in rows)
            self._conn.execute(
                f"DELETE FROM cache_entries WHERE cache_key IN ({placeholders})",  # nosec B608
                tuple(keys_to_delete),
            )
            self._conn.commit()

        return {
            # Real count of rows that actually existed and were deleted —
            # not just the size of the requested key set (a caller can ask
            # to invalidate cache_keys that don't exist; those don't count).
            "entries_invalidated": matched_count,
            "space_freed_mb": round(freed_bytes / (1024 * 1024), 6),
            "status": "success",
        }

    def purge_expired(self) -> int:
        """Delete entries past their TTL. Returns the number removed."""
        now_iso = _now().isoformat()
        cursor = self._conn.execute(
            "SELECT COUNT(*) as c FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now_iso,),
        )
        count = int(cursor.fetchone()["c"])
        self._conn.execute(
            "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now_iso,),
        )
        self._conn.commit()
        return count

    def export_entries(self) -> List[Dict[str, Any]]:
        cursor = self._conn.execute("SELECT * FROM cache_entries ORDER BY created_at")
        return [dict(row) for row in cursor.fetchall()]

    def clear(self) -> None:
        """Clear all cache data (for testing)."""
        self._conn.execute("DELETE FROM cache_entries")
        self._conn.execute("DELETE FROM cache_lookups")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
