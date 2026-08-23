"""Tests for 6D attribution model."""

from openanchor.attribution_6d import Attribution6D, Attribution6DAnalyzer


class TestAttribution6D:
    """Test 6D attribution record."""

    def test_attribution_creation(self):
        """Test creating an attribution record."""
        attr = Attribution6D(
            input_tokens=100,
            output_tokens=50,
            latency_ms=1000.0,
            cost_usd=0.01,
            quality_score=0.9,
            model_name="gpt-4",
            operation="summarization",
        )

        assert attr.total_tokens == 150
        assert attr.success is True

    def test_cost_per_token_calculation(self):
        """Test cost per token calculation."""
        attr = Attribution6D(
            input_tokens=100,
            output_tokens=100,
            latency_ms=1000.0,
            cost_usd=0.02,
            quality_score=0.85,
            model_name="gpt-3.5",
            operation="extraction",
        )

        # 0.02 / 200 tokens = 0.0001 per token
        assert abs(attr.cost_per_token - 0.0001) < 0.00001

    def test_throughput_calculation(self):
        """Test tokens per second calculation."""
        attr = Attribution6D(
            input_tokens=50,
            output_tokens=50,
            latency_ms=500.0,  # 0.5 seconds
            cost_usd=0.01,
            quality_score=0.8,
            model_name="gpt-4",
            operation="generation",
        )

        # 100 tokens / 0.5 seconds = 200 tokens/sec
        assert abs(attr.tokens_per_second - 200.0) < 0.1

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        attr = Attribution6D(
            input_tokens=100,
            output_tokens=50,
            latency_ms=1000.0,
            cost_usd=0.01,
            quality_score=0.9,
            model_name="gpt-4",
            operation="translation",
            session_id="sess_123",
        )

        d = attr.to_dict()
        assert d["total_tokens"] == 150
        assert d["model_name"] == "gpt-4"
        assert d["session_id"] == "sess_123"


class TestAttribution6DAnalyzer:
    """Test 6D attribution analyzer."""

    def test_dimension_stats_tokens(self):
        """Test token dimension statistics."""
        analyzer = Attribution6DAnalyzer()

        for i in range(5):
            attr = Attribution6D(
                input_tokens=100 + i * 10,
                output_tokens=50,
                latency_ms=1000.0,
                cost_usd=0.01,
                quality_score=0.9,
                model_name="gpt-4",
                operation="test",
            )
            analyzer.record_call(attr)

        stats = analyzer.get_dimension_stats("tokens")
        assert stats["count"] == 5
        assert stats["min"] == 150
        assert stats["max"] == 190

    def test_model_comparison(self):
        """Test model comparison."""
        analyzer = Attribution6DAnalyzer()

        # Add GPT-4 calls
        for _ in range(3):
            analyzer.record_call(
                Attribution6D(
                    input_tokens=100,
                    output_tokens=100,
                    latency_ms=1000.0,
                    cost_usd=0.02,
                    quality_score=0.95,
                    model_name="gpt-4",
                    operation="test",
                )
            )

        # Add GPT-3.5 calls
        for _ in range(2):
            analyzer.record_call(
                Attribution6D(
                    input_tokens=100,
                    output_tokens=50,
                    latency_ms=500.0,
                    cost_usd=0.01,
                    quality_score=0.80,
                    model_name="gpt-3.5",
                    operation="test",
                )
            )

        comparison = analyzer.get_model_comparison()
        assert "gpt-4" in comparison
        assert "gpt-3.5" in comparison
        assert comparison["gpt-4"]["call_count"] == 3
        assert comparison["gpt-3.5"]["call_count"] == 2

    def test_operation_breakdown(self):
        """Test operation breakdown."""
        analyzer = Attribution6DAnalyzer()

        # Summarization calls
        for _ in range(3):
            analyzer.record_call(
                Attribution6D(
                    input_tokens=500,
                    output_tokens=100,
                    latency_ms=2000.0,
                    cost_usd=0.05,
                    quality_score=0.9,
                    model_name="gpt-4",
                    operation="summarization",
                )
            )

        # Translation calls
        for _ in range(2):
            analyzer.record_call(
                Attribution6D(
                    input_tokens=200,
                    output_tokens=200,
                    latency_ms=1000.0,
                    cost_usd=0.02,
                    quality_score=0.85,
                    model_name="gpt-4",
                    operation="translation",
                )
            )

        breakdown = analyzer.get_operation_breakdown()
        assert "summarization" in breakdown
        assert "translation" in breakdown
        assert breakdown["summarization"]["call_count"] == 3
        assert breakdown["translation"]["call_count"] == 2

    def test_quality_efficiency_matrix(self):
        """Test quality vs efficiency ranking."""
        analyzer = Attribution6DAnalyzer()

        # Fast, high-quality model
        analyzer.record_call(
            Attribution6D(
                input_tokens=100,
                output_tokens=100,
                latency_ms=100.0,
                cost_usd=0.01,
                quality_score=0.95,
                model_name="fast-model",
                operation="test",
            )
        )

        # Slow, lower-quality model
        analyzer.record_call(
            Attribution6D(
                input_tokens=100,
                output_tokens=100,
                latency_ms=5000.0,
                cost_usd=0.01,
                quality_score=0.70,
                model_name="slow-model",
                operation="test",
            )
        )

        matrix = analyzer.get_quality_efficiency_matrix()
        assert len(matrix) == 2
        # Fast-model should rank higher
        assert matrix[0][0] == "fast-model"

    def test_anomaly_detection(self):
        """Test anomaly detection."""
        analyzer = Attribution6DAnalyzer()

        # Normal calls
        for _ in range(10):
            analyzer.record_call(
                Attribution6D(
                    input_tokens=100,
                    output_tokens=100,
                    latency_ms=1000.0,
                    cost_usd=0.01,
                    quality_score=0.9,
                    model_name="gpt-4",
                    operation="test",
                )
            )

        # Anomalous call - much higher latency
        analyzer.record_call(
            Attribution6D(
                input_tokens=100,
                output_tokens=100,
                latency_ms=10000.0,  # 10x higher
                cost_usd=0.01,
                quality_score=0.9,
                model_name="gpt-4",
                operation="test",
            )
        )

        anomalies = analyzer.get_anomalies(threshold_stdev=1.0)
        assert "latency" in anomalies

    def test_summary_report(self):
        """Test comprehensive summary."""
        analyzer = Attribution6DAnalyzer()

        for i in range(5):
            analyzer.record_call(
                Attribution6D(
                    input_tokens=100 + i * 10,
                    output_tokens=50,
                    latency_ms=1000.0 + i * 100,
                    cost_usd=0.01 + i * 0.001,
                    quality_score=0.85 + i * 0.01,
                    model_name="gpt-4",
                    operation="test",
                )
            )

        summary = analyzer.get_summary()
        assert summary["total_calls"] == 5
        assert "dimensions" in summary
        assert "models" in summary
        assert "operations" in summary
