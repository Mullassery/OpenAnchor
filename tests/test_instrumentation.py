"""Auto-instrumentation mapping tests with a duck-typed OTEL readable span."""

from __future__ import annotations

from types import SimpleNamespace

from openanchor import TokenCollector
from openanchor.instrumentation import OpenAnchorSpanProcessor


class _Context:
    trace_id = 0x1234
    span_id = 0x5678


class _Span:
    def __init__(self, name, attributes, start=1_000_000_000, end=1_250_000_000):
        self.name = name
        self.attributes = attributes
        self.start_time = start
        self.end_time = end
        self.context = _Context()
        self.instrumentation_scope = SimpleNamespace(name="opentelemetry.instrumentation.openai")


def test_processor_captures_tokens_and_metadata():
    collector = TokenCollector()
    processor = OpenAnchorSpanProcessor(collector)
    processor.on_end(
        _Span(
            "openai.chat",
            {
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.system": "openai",
                "gen_ai.usage.input_tokens": 12,
                "gen_ai.usage.output_tokens": 5,
                "session.id": "sess-1",
                "openinference.span.kind": "LLM",
            },
        )
    )
    events = collector.get_all_events()
    assert len(events) == 1
    event = events[0]
    assert event.model == "gpt-4o-mini"
    assert event.provider == "openai"
    assert event.tokens.input_tokens == 12
    assert event.tokens.output_tokens == 5
    assert event.session_id == "sess-1"
    assert event.latency_ms == 250.0


def test_processor_skips_own_spans_and_spans_without_tokens():
    collector = TokenCollector()
    processor = OpenAnchorSpanProcessor(collector)
    processor.on_end(_Span("openanchor.capture_event", {"gen_ai.usage.input_tokens": 10}))
    processor.on_end(_Span("db.query", {"db.system": "postgresql"}))
    assert collector.get_all_events() == []


def test_processor_deduplicates_same_span():
    collector = TokenCollector()
    processor = OpenAnchorSpanProcessor(collector)
    span = _Span("chat", {"gen_ai.usage.input_tokens": 1, "gen_ai.usage.output_tokens": 1})
    processor.on_end(span)
    processor.on_end(span)
    assert len(collector.get_all_events()) == 1
