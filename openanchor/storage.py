"""Storage layer for token events and analytics."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import TokenEvent, Attribution, SessionStats, OperationType, RequestPhase


class EventStore:
    """In-memory event store (for v0.1; PostgreSQL in v1.0)."""

    def __init__(self):
        self._events: List[TokenEvent] = []
        self._attributions: Dict[str, Attribution] = {}

    def add_event(self, event: TokenEvent) -> None:
        """Add a token event."""
        self._events.append(event)

    def get_event(self, event_id: str) -> Optional[TokenEvent]:
        """Get event by ID."""
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None

    def get_events_by_call(self, call_id: str) -> List[TokenEvent]:
        """Get all events for a call."""
        return [e for e in self._events if e.call_id == call_id]

    def get_events_by_session(self, session_id: str) -> List[TokenEvent]:
        """Get all events in a session."""
        return [e for e in self._events if e.session_id == session_id]

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


class SqliteEventStore:
    """SQLite-backed event store for v0.1 (lightweight)."""

    def __init__(self, db_path: str = "openanchor.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attributions (
                    call_id TEXT PRIMARY KEY,
                    by_phase TEXT NOT NULL,
                    by_operation TEXT NOT NULL,
                    by_prompt TEXT NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_call ON token_events(call_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_session ON token_events(session_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON token_events(timestamp)
            """)
            conn.commit()

    def add_event(self, event: TokenEvent) -> None:
        """Add a token event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
            conn.commit()

    def get_event(self, event_id: str) -> Optional[TokenEvent]:
        """Get event by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM token_events WHERE event_id = ?", (event_id,)
            )
            row = cursor.fetchone()
            return self._row_to_event(row) if row else None

    def get_events_by_call(self, call_id: str) -> List[TokenEvent]:
        """Get all events for a call."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM token_events WHERE call_id = ? ORDER BY timestamp",
                (call_id,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_events_by_session(self, session_id: str) -> List[TokenEvent]:
        """Get all events in a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM token_events WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_events_by_timerange(
        self, start: datetime, end: datetime
    ) -> List[TokenEvent]:
        """Get events within time range."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM token_events
                   WHERE timestamp >= ? AND timestamp <= ?
                   ORDER BY timestamp""",
                (start.isoformat(), end.isoformat()),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def add_attribution(self, attribution: Attribution) -> None:
        """Store attribution breakdown."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
            conn.commit()

    def get_attribution(self, call_id: str) -> Optional[Attribution]:
        """Get attribution for a call."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
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
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM token_events ORDER BY timestamp")
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def clear(self) -> None:
        """Clear all data (for testing)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM token_events")
            conn.execute("DELETE FROM attributions")
            conn.commit()

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
