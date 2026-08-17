"""Tests for LangChain middleware integration."""

import pytest

from openanchor.middleware.langchain import OpenAnchorMiddleware
from openanchor.models import OperationType


class TestOpenAnchorMiddleware:
    """Test OpenAnchor LangChain middleware."""

    def test_middleware_initialization(self):
        """Test initializing middleware."""
        middleware = OpenAnchorMiddleware(project_name="test_project")
        assert middleware.project_name == "test_project"
        assert middleware.session_id is not None

    def test_manual_capture_llm_call(self):
        """Test manually capturing an LLM call."""
        middleware = OpenAnchorMiddleware()

        middleware.capture_llm_call(
            call_id="call_1",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1000.0,
            quality_score=0.95,
            prompt_template="my_prompt",
        )

        stats = middleware.get_session_stats()
        assert stats["total_tokens"] == 150
        assert stats["total_calls"] == 1

    def test_capture_multiple_calls(self):
        """Test capturing multiple LLM calls."""
        middleware = OpenAnchorMiddleware()

        for i in range(3):
            middleware.capture_llm_call(
                call_id=f"call_{i}",
                model="gpt-4",
                input_tokens=100 + i * 10,
                output_tokens=50,
            )

        stats = middleware.get_session_stats()
        assert stats["total_calls"] == 3
        assert stats["total_tokens"] == 150 + 160 + 170

    def test_get_tokens_by_operation(self):
        """Test querying tokens by operation type."""
        middleware = OpenAnchorMiddleware()

        middleware.capture_llm_call(
            call_id="call_1",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            operation_type=OperationType.RETRIEVAL,
        )

        by_op = middleware.get_tokens_by_operation()
        assert by_op[OperationType.RETRIEVAL.value] == 150

    def test_get_tokens_by_phase(self):
        """Test querying tokens by phase."""
        middleware = OpenAnchorMiddleware()

        from openanchor.models import RequestPhase

        # Request phase
        middleware.collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=0,
            phase=RequestPhase.REQUEST,
            operation_type=OperationType.MODEL_REASONING,
        )

        # Response phase
        middleware.collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=0,
            output_tokens=50,
            phase=RequestPhase.RESPONSE,
            operation_type=OperationType.MODEL_REASONING,
        )

        by_phase = middleware.get_tokens_by_phase()
        assert by_phase["request"] == 100
        assert by_phase["response"] == 50

    def test_rank_prompts_by_efficiency(self):
        """Test ranking prompts by efficiency."""
        middleware = OpenAnchorMiddleware()

        # Efficient prompt
        middleware.capture_llm_call(
            call_id="call_1",
            model="gpt-4",
            input_tokens=100,
            output_tokens=20,
            prompt_template="efficient",
            quality_score=0.95,
        )

        # Inefficient prompt
        middleware.capture_llm_call(
            call_id="call_2",
            model="gpt-4",
            input_tokens=500,
            output_tokens=100,
            prompt_template="inefficient",
            quality_score=0.80,
        )

        ranking = middleware.rank_prompts_by_efficiency(top_n=2)
        assert len(ranking) == 2
        assert ranking[0][0] == "efficient"

    def test_get_problematic_calls(self):
        """Test finding problematic calls."""
        middleware = OpenAnchorMiddleware()

        # Problematic call (high tokens, low quality)
        middleware.capture_llm_call(
            call_id="call_1",
            model="gpt-4",
            input_tokens=5000,
            output_tokens=100,
            quality_score=0.5,
        )

        # Good call (high tokens, high quality)
        middleware.capture_llm_call(
            call_id="call_2",
            model="gpt-4",
            input_tokens=5000,
            output_tokens=100,
            quality_score=0.95,
        )

        problematic = middleware.get_problematic_calls()
        assert len(problematic) >= 1
        assert problematic[0]["call_id"] == "call_1"

    def test_get_summary(self):
        """Test getting comprehensive summary."""
        middleware = OpenAnchorMiddleware()

        middleware.capture_llm_call(
            call_id="call_1",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            latency_ms=1000.0,
            quality_score=0.95,
            operation_type=OperationType.RETRIEVAL,
        )

        summary = middleware.get_summary()
        assert summary["session_id"] == middleware.session_id
        assert summary["total_tokens"] == 150
        assert summary["total_calls"] == 1
        assert "by_operation" in summary
        assert "by_phase" in summary

    def test_get_recommendations_high_tokens(self):
        """Test recommendations for high token consumption."""
        middleware = OpenAnchorMiddleware()

        # Capture many tokens
        for i in range(10):
            middleware.capture_llm_call(
                call_id=f"call_{i}",
                model="gpt-4",
                input_tokens=1000,
                output_tokens=100,
            )

        recommendations = middleware.get_recommendations()
        assert len(recommendations) > 0
        # Should recommend reviewing prompt efficiency
        assert any("prompt efficiency" in r["action"].lower() for r in recommendations)

    def test_get_recommendations_low_quality(self):
        """Test recommendations for low quality calls."""
        middleware = OpenAnchorMiddleware()

        # Capture problematic call
        middleware.capture_llm_call(
            call_id="call_1",
            model="gpt-4",
            input_tokens=5000,
            output_tokens=100,
            quality_score=0.5,
        )

        recommendations = middleware.get_recommendations()
        assert any("low-quality" in r["action"].lower() for r in recommendations)


class _FakeRunnable:
    """Minimal stand-in for a LangChain runnable, for exercising
    WrappedRunnable.invoke() without a real LangChain dependency."""

    def __init__(self, response_metadata=None, response_text="fake response"):
        self._response_metadata = response_metadata or {}
        self._response_text = response_text
        self.invoke_calls = []

    def invoke(self, input_data, config=None):
        self.invoke_calls.append((input_data, config))
        return _FakeResult(self._response_metadata, self._response_text)

    def stream(self, input_data, config=None):
        yield _FakeResult(self._response_metadata, self._response_text)


class _FakeResult:
    def __init__(self, response_metadata, text):
        self.response_metadata = response_metadata
        self._text = text

    def __str__(self):
        return self._text


class TestWrappedRunnableInvoke:
    """WrappedRunnable.invoke() previously had zero test coverage, and had
    a real bug: it called `self._get_model_name(...)` inside a nested
    closure where `self` actually resolved to the outer
    `OpenAnchorMiddleware` instance (which has no such method) rather than
    `inner_self`/`WrappedRunnable` — an AttributeError on every real call.
    """

    def test_invoke_captures_a_token_event(self):
        middleware = OpenAnchorMiddleware(project_name="test")
        runnable = _FakeRunnable(
            response_metadata={"usage": {"input_tokens": 42, "output_tokens": 17}}
        )
        wrapped = middleware(runnable)

        result = wrapped.invoke({"model": "gpt-4", "prompt": "hi"})

        assert str(result) == "fake response"
        assert len(runnable.invoke_calls) == 1

        stats = middleware.get_session_stats()
        assert stats["total_calls"] == 1
        assert stats["total_tokens"] == 59  # 42 + 17

    def test_invoke_extracts_model_name_from_dict_input(self):
        middleware = OpenAnchorMiddleware(project_name="test")
        runnable = _FakeRunnable()
        wrapped = middleware(runnable)

        wrapped.invoke({"model": "claude-3-opus", "prompt": "hi"})

        events = middleware.store.all_events()
        assert events[0].model == "claude-3-opus"

    def test_invoke_falls_back_to_unknown_model_for_non_dict_input(self):
        middleware = OpenAnchorMiddleware(project_name="test")
        runnable = _FakeRunnable()
        wrapped = middleware(runnable)

        wrapped.invoke("a plain string prompt, not a dict")

        events = middleware.store.all_events()
        assert events[0].model == "unknown"

    def test_invoke_defaults_to_no_raw_content_capture(self):
        middleware = OpenAnchorMiddleware(project_name="test")
        runnable = _FakeRunnable(response_text="the actual llm response text")
        wrapped = middleware(runnable)

        wrapped.invoke({"model": "gpt-4", "prompt": "a secret prompt with PII a@b.com"})

        events = middleware.store.all_events()
        assert events[0].request_data["captured"] is False
        assert "excerpt" not in events[0].request_data
        assert "a@b.com" not in str(events[0].request_data)
        assert "content_sha256" in events[0].request_data

    def test_invoke_opt_in_raw_capture_redacts_pii_by_default(self):
        middleware = OpenAnchorMiddleware(project_name="test", capture_raw_content=True)
        runnable = _FakeRunnable()
        wrapped = middleware(runnable)

        wrapped.invoke({"model": "gpt-4", "prompt": "contact a@b.com for details"})

        events = middleware.store.all_events()
        assert events[0].request_data["captured"] is True
        assert "a@b.com" not in events[0].request_data["excerpt"]
        assert "<REDACTED_EMAIL>" in events[0].request_data["excerpt"]

    def test_invoke_opt_in_raw_capture_without_redaction(self):
        middleware = OpenAnchorMiddleware(
            project_name="test", capture_raw_content=True, redact_captured_content=False
        )
        runnable = _FakeRunnable()
        wrapped = middleware(runnable)

        wrapped.invoke({"model": "gpt-4", "prompt": "contact a@b.com for details"})

        events = middleware.store.all_events()
        assert "a@b.com" in events[0].request_data["excerpt"]

    def test_invoke_with_no_usage_metadata_defaults_to_zero_tokens(self):
        middleware = OpenAnchorMiddleware(project_name="test")
        runnable = _FakeRunnable(response_metadata={})
        wrapped = middleware(runnable)

        wrapped.invoke({"model": "gpt-4"})

        events = middleware.store.all_events()
        assert events[0].tokens.total_tokens == 0

    def test_invoke_propagates_runnable_exceptions(self):
        class _RaisingRunnable:
            def invoke(self, input_data, config=None):
                raise RuntimeError("boom")

        middleware = OpenAnchorMiddleware(project_name="test")
        wrapped = middleware(_RaisingRunnable())

        with pytest.raises(RuntimeError, match="boom"):
            wrapped.invoke({"model": "gpt-4"})

    def test_batch_invokes_each_input(self):
        middleware = OpenAnchorMiddleware(project_name="test")
        runnable = _FakeRunnable()
        wrapped = middleware(runnable)

        results = wrapped.batch([{"model": "gpt-4"}, {"model": "gpt-4"}])

        assert len(results) == 2
        assert len(runnable.invoke_calls) == 2

    def test_call_requires_a_runnable(self):
        middleware = OpenAnchorMiddleware(project_name="test")
        with pytest.raises(ValueError):
            middleware("not a runnable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
