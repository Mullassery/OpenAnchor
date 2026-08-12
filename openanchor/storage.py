"""Storage layer for token events and analytics."""

import json
import sqlite3
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .models import Attribution, OperationType, RequestPhase, TokenEvent


class EventStore:
    """In-memory event store (for v0.1; PostgreSQL in v1.0).

    Indexed by call_id/session_id so ``get_events_by_call``/
    ``get_events_by_session`` are O(1) dict lookups instead of O(n) scans
    over every stored event.
    """

    def __init__(self):
        self._events: List[TokenEvent] = []
        self._attributions: Dict[str, Attribution] = {}
        self._by_call: Dict[str, List[TokenEvent]] = defaultdict(list)
        self._by_session: Dict[str, List[TokenEvent]] = defaultdict(list)

    def add_event(self, event: TokenEvent) -> None:
        """Add a token event."""
        self._events.append(event)
        self._by_call[event.call_id].append(event)
        if event.session_id:
            self._by_session[event.session_id].append(event)

    def get_event(self, event_id: str) -> Optional[TokenEvent]:
        """Get event by ID."""
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None

    def get_events_by_call(self, call_id: str) -> List[TokenEvent]:
        """Get all events for a call. O(1) via index."""
        return list(self._by_call.get(call_id, []))

    def get_events_by_session(self, session_id: str) -> List[TokenEvent]:
        """Get all events in a session. O(1) via index."""
        return list(self._by_session.get(session_id, []))

    def get_events_by_timerange(
        self, start: datetime, end: datetime
    ) -> List[TokenEvent]:
        """Get events within time range."""
        return [e for e in self._events if start <= e.timestamp <= end]

    def add_attribution(self, attribution: Attribution) -> None:
        """Store attribution breakdown."""
        self._attributions[attribution.call_id] = attribution

    def get_attribution(self, call_id: str) -> Optional[Attribution]:
        """Get attribution for a call."""
        return self._attributions.get(call_id)

    def all_events(self) -> List[TokenEvent]:
        """Get all events."""
        return self._events.copy()

    def purge_older_than(self, cutoff: datetime) -> int:
        """Remove events older than ``cutoff``. Returns the number removed."""
        keep = [e for e in self._events if e.timestamp >= cutoff]
        removed = len(self._events) - len(keep)
        if removed:
            self._events = keep
            self._by_call = defaultdict(list)
            self._by_session = defaultdict(list)
            for e in keep:
                self._by_call[e.call_id].append(e)
                if e.session_id:
                    self._by_session[e.session_id].append(e)
        return removed

    def clear(self) -> None:
        """Clear all data."""
        self._events = []
        self._attributions = {}
        self._by_call = defaultdict(list)
        self._by_session = defaultdict(list)


class SqliteEventStore:
    """SQLite-backed event store.

    Performance: reuses a single connection in WAL mode (rather than
    opening/closing a fresh ``sqlite3.connect()`` per call, which was the
    collector's hot-path bottleneck), so concurrent readers don't block
    writers and repeated ``add_event`` calls avoid per-call connection
    setup cost.

    Privacy/retention: supports an optional ``retention_days`` TTL. When
    set, events older than the retention window are purged automatically
    every ``auto_purge_every`` writes (in addition to the existing manual
    ``clear()``/``purge_expired()``), so captured call data doesn't
    accumulate indefinitely by default once a retention policy is
    configured.
    """

    def __init__(
        self,
        db_path: str = "openanchor.db",
        retention_days: Optional[int] = None,
        auto_purge_every: int = 500,
    ):
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.auto_purge_every = auto_purge_every
        self._write_count = 0
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS token_events (
                    event_id TEXT PRIMARY KEY,
                    call_id TEXT NOT NULL,
                    session_id TEXT,
                    timestamp TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    prompt_template TEXT,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    latency_ms REAL,
                    ttft_ms REAL,
                    quality_score REAL,
                    request_data TEXT,
                    response_data TEXT,
                    tags TEXT
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS attributions (
                    call_id TEXT PRIMARY KEY,
                    by_phase TEXT NOT NULL,
                    by_operation TEXT NOT NULL,
                    by_prompt TEXT NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_call ON token_events(call_id)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_session ON token_events(session_id)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON token_events(timestamp)"
            )
            self._conn.commit()

    def add_event(self, event: TokenEvent) -> None:
        """Add a token event, reusing the shared connection."""
        with self._lock:
            self._conn.execute("""
                INSERT INTO token_events (
                    event_id, call_id, session_id, timestamp, phase,
                    operation_type, prompt_template, model, provider,
                    input_tokens, output_tokens, latency_ms, ttft_ms,
                    quality_score, request_data, response_data, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.call_id,
                event.session_id,
                event.timestamp.isoformat(),
                event.phase.value,
                event.operation_type.value,
                event.prompt_template,
                event.model,
                event.provider,
                event.tokens.input_tokens,
                event.tokens.output_tokens,
                event.latency_ms,
                event.ttft_ms,
                event.quality_score,
                json.dumps(event.request_data) if event.request_data else None,
                json.dumps(event.response_data) if event.response_data else None,
                json.dumps(event.tags) if event.tags else None,
            ))
            self._conn.commit()
            self._write_count += 1

            should_purge = (
                self.retention_days is not None
                and self.auto_purge_every > 0
                and self._write_count % self.auto_purge_every == 0
            )

        # Purge outside the lock's critical section for the insert, but
        # purge_expired() takes the lock itself.
        if should_purge:
            self.purge_expired()

    def purge_expired(self) -> int:
        """Delete events older than ``retention_days``. No-op if unset.

        Returns the number of events removed.
        """
        if self.retention_days is None:
            return 0
        cutoff = (datetime.utcnow() - timedelta(days=self.retention_days)).isoformat()
        with self._lock:
            cursor = self._conn.execute(
                "SELECT COUNT(*) as c FROM token_events WHERE timestamp < ?", (cutoff,)
            )
            count = int(cursor.fetchone()["c"])
            if count:
                self._conn.execute("DELETE FROM token_events WHERE timestamp < ?", (cutoff,))
                self._conn.commit()
            return count

    def get_event(self, event_id: str) -> Optional[TokenEvent]:
        """Get event by ID."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT * FROM token_events WHERE event_id = ?", (event_id,)
            )
            row = cursor.fetchone()
            return self._row_to_event(row) if row else None

    def get_events_by_call(self, call_id: str) -> List[TokenEvent]:
        """Get all events for a call."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT * FROM token_events WHERE call_id = ? ORDER BY timestamp",
                (call_id,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_events_by_session(self, session_id: str) -> List[TokenEvent]:
        """Get all events in a session."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT * FROM token_events WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_events_by_timerange(
        self, start: datetime, end: datetime
    ) -> List[TokenEvent]:
        """Get events within time range."""
        with self._lock:
            cursor = self._conn.execute(
                """SELECT * FROM token_events
                   WHERE timestamp >= ? AND timestamp <= ?
                   ORDER BY timestamp""",
                (start.isoformat(), end.isoformat()),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def add_attribution(self, attribution: Attribution) -> None:
        """Store attribution breakdown."""
        with self._lock:
            self._conn.execute("""
                INSERT OR REPLACE INTO attributions (
                    call_id, by_phase, by_operation, by_prompt, total_tokens, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                attribution.call_id,
                json.dumps({k.value: v for k, v in attribution.by_phase.items()}),
                json.dumps({k.value: v for k, v in attribution.by_operation.items()}),
                json.dumps(attribution.by_prompt_template),
                attribution.total_tokens,
                attribution.created_at.isoformat(),
            ))
            self._conn.commit()

    def get_attribution(self, call_id: str) -> Optional[Attribution]:
        """Get attribution for a call."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT * FROM attributions WHERE call_id = ?", (call_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            by_phase = {
                RequestPhase(k): v
                for k, v in json.loads(row["by_phase"]).items()
            }
            by_operation = {
                OperationType(k): v
                for k, v in json.loads(row["by_operation"]).items()
            }
            return Attribution(
                call_id=row["call_id"],
                by_phase=by_phase,
                by_operation=by_operation,
                by_prompt_template=json.loads(row["by_prompt"]),
                total_tokens=row["total_tokens"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def all_events(self) -> List[TokenEvent]:
        """Get all events."""
        with self._lock:
            cursor = self._conn.execute("SELECT * FROM token_events ORDER BY timestamp")
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def clear(self) -> None:
        """Clear all data (for testing)."""
        with self._lock:
            self._conn.execute("DELETE FROM token_events")
            self._conn.execute("DELETE FROM attributions")
            self._conn.commit()

    def close(self) -> None:
        """Close the underlying connection."""
        with self._lock:
            self._conn.close()

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> TokenEvent:
        """Convert database row to TokenEvent."""
        from .models import TokenConsumption

        return TokenEvent(
            event_id=row["event_id"],
            call_id=row["call_id"],
            session_id=row["session_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            phase=RequestPhase(row["phase"]),
            operation_type=OperationType(row["operation_type"]),
            prompt_template=row["prompt_template"],
            model=row["model"],
            provider=row["provider"],
            tokens=TokenConsumption(
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
            ),
            latency_ms=row["latency_ms"],
            ttft_ms=row["ttft_ms"],
            quality_score=row["quality_score"],
            request_data=json.loads(row["request_data"]) if row["request_data"] else {},
            response_data=json.loads(row["response_data"]) if row["response_data"] else {},
            tags=json.loads(row["tags"]) if row["tags"] else {},
        )
