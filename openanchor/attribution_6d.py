"""6D Attribution Model - Analyze LLM requests across 6 dimensions: tokens, latency, cost, quality, model, and phase."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Quality(Enum):
    """Quality levels for LLM outputs."""

    CRITICAL = 0.0
    POOR = 0.3
    FAIR = 0.5
    GOOD = 0.75
    EXCELLENT = 1.0


@dataclass
class Attribution6D:
    """6-dimensional attribution of an LLM call."""

    # Dimension 1: Tokens
    input_tokens: int
    output_tokens: int

    # Dimension 2: Latency
    latency_ms: float

    # Dimension 3: Cost
    cost_usd: float

    # Dimension 4: Quality
    quality_score: float  # 0.0-1.0

    # Dimension 5: Model
    model_name: str

    # Dimension 6: Phase/Operation
    operation: str

    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    success: bool = True

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def cost_per_token(self) -> float:
        """Cost per token."""
        if self.total_tokens == 0:
            return 0.0
        return self.cost_usd / self.total_tokens

    @property
    def tokens_per_second(self) -> float:
        """Throughput in tokens/sec."""
        if self.latency_ms == 0:
            return 0.0
        return self.total_tokens / (self.latency_ms / 1000.0)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "quality_score": self.quality_score,
            "model_name": self.model_name,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "success": self.success,
            "cost_per_token": self.cost_per_token,
            "tokens_per_second": self.tokens_per_second,
        }


class Attribution6DAnalyzer:
    """Analyze LLM calls across all 6 dimensions."""

    def __init__(self):
        self.calls: List[Attribution6D] = []

    def record_call(self, attribution: Attribution6D):
        """Record a new LLM call."""
        self.calls.append(attribution)

    def get_dimension_stats(self, dimension: str) -> Dict:
        """Get statistics for a specific dimension."""
        if not self.calls:
            return {}

        if dimension == "tokens":
            values = [c.total_tokens for c in self.calls]
        elif dimension == "latency":
            values = [c.latency_ms for c in self.calls]
        elif dimension == "cost":
            values = [c.cost_usd for c in self.calls]
        elif dimension == "quality":
            values = [c.quality_score for c in self.calls]
        elif dimension == "throughput":
            values = [c.tokens_per_second for c in self.calls]
        elif dimension == "cost_per_token":
            values = [c.cost_per_token for c in self.calls]
        else:
            return {}

        return {
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "sum": sum(values),
            "count": len(values),
        }

    def get_model_comparison(self) -> Dict:
        """Compare performance across models."""
        by_model: Dict[str, List[Attribution6D]] = {}

        for call in self.calls:
            if call.model_name not in by_model:
                by_model[call.model_name] = []
            by_model[call.model_name].append(call)

        comparison = {}
        for model, calls in by_model.items():
            if not calls:
                continue

            comparison[model] = {
                "call_count": len(calls),
                "avg_tokens": sum(c.total_tokens for c in calls) / len(calls),
                "avg_latency_ms": sum(c.latency_ms for c in calls) / len(calls),
                "total_cost": sum(c.cost_usd for c in calls),
                "avg_quality": sum(c.quality_score for c in calls) / len(calls),
                "avg_cost_per_token": sum(c.cost_per_token for c in calls) / len(calls),
                "success_rate": sum(1 for c in calls if c.success) / len(calls),
            }

        return comparison

    def get_operation_breakdown(self) -> Dict:
        """Break down metrics by operation/phase."""
        by_operation: Dict[str, List[Attribution6D]] = {}

        for call in self.calls:
            if call.operation not in by_operation:
                by_operation[call.operation] = []
            by_operation[call.operation].append(call)

        breakdown = {}
        for operation, calls in by_operation.items():
            if not calls:
                continue

            breakdown[operation] = {
                "call_count": len(calls),
                "total_tokens": sum(c.total_tokens for c in calls),
                "total_cost": sum(c.cost_usd for c in calls),
                "avg_quality": sum(c.quality_score for c in calls) / len(calls),
                "avg_latency_ms": sum(c.latency_ms for c in calls) / len(calls),
            }

        return breakdown

    def get_quality_efficiency_matrix(self) -> List[Tuple[str, float, float]]:
        """
        Get quality vs efficiency ranking for each model.

        Returns:
            List of (model_name, quality_score, efficiency_score)
        """
        by_model: Dict[str, List[Attribution6D]] = {}

        for call in self.calls:
            if call.model_name not in by_model:
                by_model[call.model_name] = []
            by_model[call.model_name].append(call)

        matrix = []
        for model, calls in by_model.items():
            avg_quality = sum(c.quality_score for c in calls) / len(calls)
            # Efficiency = tokens_per_second / cost_per_token (higher is better)
            avg_tps = sum(c.tokens_per_second for c in calls) / len(calls)
            avg_cpt = sum(c.cost_per_token for c in calls) / len(calls)
            efficiency = avg_tps / max(avg_cpt, 0.00001)  # Avoid division by zero

            matrix.append((model, avg_quality, efficiency))

        return sorted(matrix, key=lambda x: (x[1], x[2]), reverse=True)

    def get_anomalies(self, threshold_stdev: float = 2.0) -> Dict:
        """Find anomalous calls (outliers in any dimension)."""
        anomalies = {}

        dimensions = {
            "tokens": [c.total_tokens for c in self.calls],
            "latency": [c.latency_ms for c in self.calls],
            "cost": [c.cost_usd for c in self.calls],
        }

        for dim_name, values in dimensions.items():
            if len(values) < 2:
                continue

            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            threshold = mean + (stdev * threshold_stdev)

            anomalous = [(i, v) for i, v in enumerate(values) if v > threshold]
            if anomalous:
                anomalies[dim_name] = [
                    {
                        "call_index": idx,
                        "value": val,
                        "threshold": threshold,
                        "stdevs_above_mean": (val - mean) / stdev if stdev > 0 else 0,
                    }
                    for idx, val in anomalous
                ]

        return anomalies

    def get_summary(self) -> Dict:
        """Get comprehensive summary of all 6D attributes."""
        if not self.calls:
            return {"status": "no_data"}

        return {
            "total_calls": len(self.calls),
            "date_range": {
                "start": min(c.timestamp for c in self.calls).isoformat(),
                "end": max(c.timestamp for c in self.calls).isoformat(),
            },
            "dimensions": {
                "tokens": self.get_dimension_stats("tokens"),
                "latency_ms": self.get_dimension_stats("latency"),
                "cost_usd": self.get_dimension_stats("cost"),
                "quality_score": self.get_dimension_stats("quality"),
                "tokens_per_second": self.get_dimension_stats("throughput"),
            },
            "models": self.get_model_comparison(),
            "operations": self.get_operation_breakdown(),
            "quality_efficiency": self.get_quality_efficiency_matrix(),
            "anomalies": self.get_anomalies(),
        }
