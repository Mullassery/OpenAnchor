"""Tests for core OpenAnchor components."""

import pytest
from datetime import datetime
from openanchor.models import (
    TokenEvent,
    TokenConsumption,
    Attribution,
    SessionStats,
    OperationType,
    RequestPhase,
)
from openanchor.collector import TokenCollector
from openanchor.storage import EventStore
from openanchor.attribution import AttributionModel
from openanchor.analytics import Analytics


class TestTokenEvent:
    """Test TokenEvent model."""

    def test_create_event(self):
        """Test creating a token event."""
        event = TokenEvent(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            tokens=TokenConsumption(input_tokens=100, output_tokens=50),
        )
        assert event.call_id == "call_1"
        assert event.tokens.total_tokens == 150

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = TokenEvent(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            tokens=TokenConsumption(input_tokens=100, output_tokens=50),
            phase=RequestPhase.RESPONSE,
            operation_type=OperationType.MODEL_REASONING,
        )
        data = event.to_dict()
        assert data["call_id"] == "call_1"
        assert data["tokens"]["total_tokens"] == 150
        assert data["phase"] == "response"


class TestTokenCollector:
    """Test TokenCollector."""

    def test_capture_event(self):
        """Test capturing an event."""
        collector = TokenCollector()

        event = collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
        )

        assert event.call_id == "call_1"
        assert event.tokens.total_tokens == 150

    def test_capture_multiple_events(self):
        """Test capturing multiple events for same call."""
        collector = TokenCollector()
        collector.set_session("session_1")

        for i in range(3):
            collector.capture_event(
                call_id="call_1",
                model="gpt-4",
                provider="openai",
                input_tokens=100 + i * 10,
                output_tokens=50,
            )

        events = collector.get_events_for_call("call_1")
        assert len(events) == 3
        assert sum(e.tokens.input_tokens for e in events) == 330

    def test_get_events_by_session(self):
        """Test retrieving events by session."""
        collector = TokenCollector()
        collector.set_session("session_1")

        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
        )

        events = collector.get_events_for_session("session_1")
        assert len(events) == 1
        assert events[0].session_id == "session_1"

    def test_compute_call_stats(self):
        """Test computing call statistics."""
        collector = TokenCollector()

        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1000.0,
            quality_score=0.95,
        )

        stats = collector.compute_call_stats("call_1")
        assert stats["total_tokens"] == 150
        assert stats["total_input_tokens"] == 100
        assert stats["total_output_tokens"] == 50
        assert stats["avg_latency_ms"] == 1000.0
        assert stats["avg_quality_score"] == 0.95

    def test_compute_session_stats(self):
        """Test computing session statistics."""
        collector = TokenCollector()
        collector.set_session("session_1")

        for i in range(3):
            collector.capture_event(
                call_id=f"call_{i}",
                model="gpt-4",
                provider="openai",
                input_tokens=100,
                output_tokens=50,
                operation_type=OperationType.MODEL_REASONING,
            )

        stats = collector.compute_session_stats("session_1")
        assert stats.session_id == "session_1"
        assert stats.total_tokens == 450
        assert stats.total_calls == 3


class TestAttributionModel:
    """Test AttributionModel."""

    def test_analyze_call_simple(self):
        """Test analyzing a simple call."""
        store = EventStore()
        collector = TokenCollector(store)

        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            operation_type=OperationType.SYSTEM_PROMPT,
        )

        attribution = AttributionModel(store).analyze_call("call_1")
        assert attribution.call_id == "call_1"
        assert attribution.total_tokens == 150
        assert (
            attribution.by_operation[OperationType.SYSTEM_PROMPT] == 150
        )

    def test_analyze_call_multiple_operations(self):
        """Test analyzing call with multiple operation types."""
        store = EventStore()
        collector = TokenCollector(store)

        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=0,
            operation_type=OperationType.SYSTEM_PROMPT,
        )

        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=200,
            output_tokens=0,
            operation_type=OperationType.RETRIEVAL,
        )

        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=0,
            output_tokens=50,
            operation_type=OperationType.MODEL_REASONING,
        )

        attribution = AttributionModel(store).analyze_call("call_1")
        assert attribution.total_tokens == 350
        assert attribution.by_operation[OperationType.SYSTEM_PROMPT] == 100
        assert attribution.by_operation[OperationType.RETRIEVAL] == 200
        assert attribution.by_operation[OperationType.MODEL_REASONING] == 50

    def test_get_operation_breakdown(self):
        """Test getting operation breakdown for session."""
        store = EventStore()
        collector = TokenCollector(store)
        collector.set_session("session_1")

        for op_type, tokens in [
            (OperationType.SYSTEM_PROMPT, 100),
            (OperationType.RETRIEVAL, 200),
            (OperationType.MODEL_REASONING, 150),
        ]:
            collector.capture_event(
                call_id=f"call_{op_type.value}",
                model="gpt-4",
                provider="openai",
                input_tokens=tokens,
                output_tokens=0,
                operation_type=op_type,
            )

        breakdown = AttributionModel(store).get_operation_breakdown("session_1")
        assert breakdown[OperationType.SYSTEM_PROMPT.value] == 100
        assert breakdown[OperationType.RETRIEVAL.value] == 200
        assert breakdown[OperationType.MODEL_REASONING.value] == 150

    def test_rank_prompts_by_efficiency(self):
        """Test ranking prompts by efficiency."""
        store = EventStore()
        collector = TokenCollector(store)
        collector.set_session("session_1")

        # High efficiency prompt (few tokens, high quality)
        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=20,
            prompt_template="efficient_prompt",
            quality_score=0.95,
        )

        # Low efficiency prompt (many tokens, lower quality)
        collector.capture_event(
            call_id="call_2",
            model="gpt-4",
            provider="openai",
            input_tokens=500,
            output_tokens=100,
            prompt_template="inefficient_prompt",
            quality_score=0.80,
        )

        ranking = AttributionModel(store).rank_prompts_by_efficiency("session_1")
        assert len(ranking) == 2
        assert ranking[0][0] == "efficient_prompt"
        assert ranking[0][1] > ranking[1][1]


class TestAnalytics:
    """Test Analytics API."""

    def test_get_tokens_by_operation(self):
        """Test token breakdown by operation."""
        store = EventStore()
        collector = TokenCollector(store)
        attribution = AttributionModel(store)
        analytics = Analytics(collector, attribution)

        collector.set_session("session_1")
        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            operation_type=OperationType.RETRIEVAL,
        )

        breakdown = analytics.get_tokens_by_operation("session_1")
        assert breakdown[OperationType.RETRIEVAL.value] == 150

    def test_get_tokens_by_phase(self):
        """Test token breakdown by phase."""
        store = EventStore()
        collector = TokenCollector(store)
        attribution = AttributionModel(store)
        analytics = Analytics(collector, attribution)

        collector.set_session("session_1")
        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=0,
            phase=RequestPhase.REQUEST,
        )

        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=0,
            output_tokens=50,
            phase=RequestPhase.RESPONSE,
        )

        breakdown = analytics.get_tokens_by_phase("session_1")
        assert breakdown["request"] == 100
        assert breakdown["response"] == 50

    def test_get_problematic_calls(self):
        """Test finding problematic calls (high tokens, low quality)."""
        store = EventStore()
        collector = TokenCollector(store)
        attribution = AttributionModel(store)
        analytics = Analytics(collector, attribution)

        collector.set_session("session_1")

        # Problematic: high tokens, low quality
        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=5000,
            output_tokens=100,
            quality_score=0.5,
        )

        # Good: high tokens, high quality
        collector.capture_event(
            call_id="call_2",
            model="gpt-4",
            provider="openai",
            input_tokens=5000,
            output_tokens=100,
            quality_score=0.95,
        )

        problematic = analytics.get_problematic_calls("session_1")
        assert len(problematic) >= 1
        assert problematic[0]["call_id"] == "call_1"

    def test_get_summary(self):
        """Test getting session summary."""
        store = EventStore()
        collector = TokenCollector(store)
        attribution = AttributionModel(store)
        analytics = Analytics(collector, attribution)

        collector.set_session("session_1")
        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
        )

        summary = analytics.get_summary("session_1")
        assert summary["session_id"] == "session_1"
        assert summary["total_tokens"] == 150
        assert summary["total_calls"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
