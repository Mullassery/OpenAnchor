"""Tests for openanchor/storage.py: EventStore indexing and SqliteEventStore
(persistence, connection reuse, retention/TTL purge, indexing).

SqliteEventStore previously had zero test coverage.
"""

from datetime import datetime, timedelta

import pytest

from openanchor.models import OperationType, RequestPhase, TokenConsumption, TokenEvent
from openanchor.storage import EventStore, SqliteEventStore


def _make_event(call_id="call_1", session_id="session_1", input_tokens=10, output_tokens=5, timestamp=None):
    return TokenEvent(
        call_id=call_id,
        session_id=session_id,
        model="gpt-4",
        provider="openai",
        tokens=TokenConsumption(input_tokens=input_tokens, output_tokens=output_tokens),
        timestamp=timestamp or datetime.utcnow(),
    )


class TestEventStoreIndexing:
    def test_get_events_by_call_uses_index(self):
        store = EventStore()
        store.add_event(_make_event(call_id="a"))
        store.add_event(_make_event(call_id="b"))
        store.add_event(_make_event(call_id="a"))

        assert len(store.get_events_by_call("a")) == 2
        assert len(store.get_events_by_call("b")) == 1
        assert store.get_events_by_call("nonexistent") == []

    def test_get_events_by_session_uses_index(self):
        store = EventStore()
        store.add_event(_make_event(session_id="s1"))
        store.add_event(_make_event(session_id="s2"))

        assert len(store.get_events_by_session("s1")) == 1
        assert store.get_events_by_session("nonexistent") == []

    def test_event_without_session_id_not_indexed_by_session(self):
        store = EventStore()
        event = _make_event()
        event.session_id = None
        store.add_event(event)
        assert store.all_events() == [event]

    def test_purge_older_than_removes_old_events_and_reindexes(self):
        store = EventStore()
        old = _make_event(call_id="old", timestamp=datetime.utcnow() - timedelta(days=10))
        new = _make_event(call_id="new", timestamp=datetime.utcnow())
        store.add_event(old)
        store.add_event(new)

        removed = store.purge_older_than(datetime.utcnow() - timedelta(days=1))
        assert removed == 1
        assert store.get_events_by_call("old") == []
        assert len(store.get_events_by_call("new")) == 1
        assert len(store.all_events()) == 1

    def test_clear_resets_indexes(self):
        store = EventStore()
        store.add_event(_make_event(call_id="a"))
        store.clear()
        assert store.all_events() == []
        assert store.get_events_by_call("a") == []


class TestSqliteEventStoreCrud:
    @pytest.fixture
    def store(self, tmp_path):
        s = SqliteEventStore(db_path=str(tmp_path / "events.db"))
        yield s
        s.close()

    def test_add_and_get_event(self, store):
        event = _make_event()
        store.add_event(event)
        fetched = store.get_event(event.event_id)
        assert fetched is not None
        assert fetched.call_id == event.call_id
        assert fetched.tokens.total_tokens == 15

    def test_get_events_by_call(self, store):
        store.add_event(_make_event(call_id="a"))
        store.add_event(_make_event(call_id="a"))
        store.add_event(_make_event(call_id="b"))
        assert len(store.get_events_by_call("a")) == 2
        assert len(store.get_events_by_call("b")) == 1

    def test_get_events_by_session(self, store):
        store.add_event(_make_event(session_id="s1"))
        assert len(store.get_events_by_session("s1")) == 1

    def test_all_events_ordered_by_timestamp(self, store):
        e1 = _make_event(call_id="1", timestamp=datetime(2025, 1, 1))
        e2 = _make_event(call_id="2", timestamp=datetime(2025, 1, 2))
        store.add_event(e2)
        store.add_event(e1)
        events = store.all_events()
        assert [e.call_id for e in events] == ["1", "2"]

    def test_request_response_data_roundtrip_as_json(self, store):
        event = _make_event()
        event.request_data = {"content_sha256": "abc", "captured": False}
        event.response_data = {"content_sha256": "def", "captured": False}
        store.add_event(event)
        fetched = store.get_event(event.event_id)
        assert fetched.request_data == {"content_sha256": "abc", "captured": False}
        assert fetched.response_data == {"content_sha256": "def", "captured": False}

    def test_clear_removes_all_data(self, store):
        store.add_event(_make_event())
        store.clear()
        assert store.all_events() == []

    def test_attribution_roundtrip(self, store):
        from openanchor.models import Attribution

        attribution = Attribution(
            call_id="call_1",
            by_phase={RequestPhase.REQUEST: 100},
            by_operation={OperationType.RETRIEVAL: 100},
            by_prompt_template={"tpl": 100},
            total_tokens=100,
        )
        store.add_attribution(attribution)
        fetched = store.get_attribution("call_1")
        assert fetched.total_tokens == 100
        assert fetched.by_phase[RequestPhase.REQUEST] == 100

    def test_connection_is_reused_not_reopened_per_call(self, store):
        """Performance fix: add_event should not open a fresh sqlite3.connect() each time."""
        conn_id_before = id(store._conn)
        for i in range(20):
            store.add_event(_make_event(call_id=f"c{i}"))
        assert id(store._conn) == conn_id_before

    def test_wal_mode_enabled(self, store):
        cursor = store._conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        assert mode.lower() == "wal"


class TestSqliteEventStoreRetention:
    def test_no_retention_by_default(self, tmp_path):
        store = SqliteEventStore(db_path=str(tmp_path / "e.db"))
        assert store.retention_days is None
        assert store.purge_expired() == 0
        store.close()

    def test_purge_expired_removes_old_events(self, tmp_path):
        store = SqliteEventStore(db_path=str(tmp_path / "e.db"), retention_days=7)
        old_event = _make_event(call_id="old", timestamp=datetime.utcnow() - timedelta(days=30))
        new_event = _make_event(call_id="new", timestamp=datetime.utcnow())
        store.add_event(old_event)
        store.add_event(new_event)

        removed = store.purge_expired()
        assert removed == 1
        remaining = store.all_events()
        assert len(remaining) == 1
        assert remaining[0].call_id == "new"
        store.close()

    def test_auto_purge_triggers_after_configured_write_count(self, tmp_path):
        store = SqliteEventStore(
            db_path=str(tmp_path / "e.db"), retention_days=7, auto_purge_every=3
        )
        store.add_event(_make_event(call_id="old", timestamp=datetime.utcnow() - timedelta(days=30)))
        # Two more writes -> 3rd write triggers auto-purge.
        store.add_event(_make_event(call_id="new1"))
        store.add_event(_make_event(call_id="new2"))

        remaining_call_ids = {e.call_id for e in store.all_events()}
        assert "old" not in remaining_call_ids
        store.close()
