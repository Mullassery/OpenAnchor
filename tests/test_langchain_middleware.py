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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
