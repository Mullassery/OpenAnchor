"""OKF Optimization Tracking for OpenAnchor.

Track which optimization strategies work best, measure success rates,
and recommend optimizations based on historical performance.
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class OptimizationResult:
    """Result of applying an optimization strategy."""

    strategy: str  # e.g., "prompt_compression", "token_caching", "model_downgrade"
    baseline_cost: float
    optimized_cost: float
    reduction_pct: float
    success: bool
    model: str
    domain: str
    timestamp: str


class OKFOptimizationTracking:
    """Track optimization strategy effectiveness."""

    def __init__(self, tracking_dir: Path = None):
        self.tracking_dir = tracking_dir or Path.cwd() / "optimization_tracking"
        self.tracking_dir.mkdir(exist_ok=True)

    def record_optimization(self, strategy: str, baseline_cost: float,
                          optimized_cost: float, success: bool,
                          model: str, domain: str = "default") -> None:
        """Record optimization attempt."""
        reduction_pct = ((baseline_cost - optimized_cost) / baseline_cost) * 100

        result = OptimizationResult(
            strategy=strategy,
            baseline_cost=baseline_cost,
            optimized_cost=optimized_cost,
            reduction_pct=reduction_pct,
            success=success,
            model=model,
            domain=domain,
            timestamp=datetime.now().isoformat()
        )

        # Save to strategy-specific log
        log_file = self.tracking_dir / f"strategy_{strategy}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps({
                'strategy': result.strategy,
                'baseline_cost': result.baseline_cost,
                'optimized_cost': result.optimized_cost,
                'reduction_pct': result.reduction_pct,
                'success': result.success,
                'model': result.model,
                'domain': result.domain,
                'timestamp': result.timestamp
            }) + '\n')

    def get_strategy_effectiveness(self, strategy: str) -> Dict[str, float]:
        """Get success metrics for optimization strategy."""
        log_file = self.tracking_dir / f"strategy_{strategy}.jsonl"
        if not log_file.exists():
            return {'success_rate': 0.0, 'avg_savings': 0.0, 'total_trials': 0}

        results = []
        with open(log_file) as f:
            for line in f:
                results.append(json.loads(line))

        if not results:
            return {'success_rate': 0.0, 'avg_savings': 0.0, 'total_trials': 0}

        successes = sum(1 for r in results if r['success'])
        avg_savings = sum(r['reduction_pct'] for r in results) / len(results)

        return {
            'success_rate': (successes / len(results)) * 100,
            'avg_savings': avg_savings,
            'total_trials': len(results),
            'sample_size': len(results)
        }

    def recommend_optimizations(self, model: str, domain: str = "default",
                               top_n: int = 3) -> List[Dict]:
        """Recommend best optimizations for model-domain combo."""
        strategies = {}

        # Scan all strategy logs
        for strategy_file in self.tracking_dir.glob("strategy_*.jsonl"):
            strategy_name = strategy_file.stem.replace("strategy_", "")
            effectiveness = self.get_strategy_effectiveness(strategy_name)

            # Filter by model and domain
            relevant_results = self._get_results_for_model_domain(strategy_file, model, domain)
            if relevant_results:
                effectiveness['avg_savings_for_model'] = \
                    sum(r['reduction_pct'] for r in relevant_results) / len(relevant_results)
                strategies[strategy_name] = effectiveness

        # Sort by effectiveness and return top N
        sorted_strategies = sorted(
            strategies.items(),
            key=lambda x: x[1].get('avg_savings_for_model', x[1]['avg_savings']),
            reverse=True
        )

        return [
            {
                'strategy': name,
                'effectiveness': metrics
            }
            for name, metrics in sorted_strategies[:top_n]
        ]

    def _get_results_for_model_domain(self, log_file: Path, model: str,
                                     domain: str) -> List[Dict]:
        """Get optimization results for specific model-domain."""
        results = []

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry['model'] == model and entry['domain'] == domain:
                    results.append(entry)

        return results


class OptimizationLeaderboard:
    """Rank strategies and models by cost efficiency."""

    def __init__(self, tracking_dir: Path):
        self.tracking_dir = tracking_dir

    def get_best_strategies(self, limit: int = 10) -> List[Dict]:
        """Get highest-impact optimization strategies."""
        all_results = {}

        for strategy_file in self.tracking_dir.glob("strategy_*.jsonl"):
            strategy = strategy_file.stem.replace("strategy_", "")
            results = []

            with open(strategy_file) as f:
                for line in f:
                    results.append(json.loads(line))

            if results:
                successful = [r for r in results if r['success']]
                if successful:
                    avg_savings = sum(r['reduction_pct'] for r in successful) / len(successful)
                    success_rate = (len(successful) / len(results)) * 100

                    all_results[strategy] = {
                        'avg_savings_pct': avg_savings,
                        'success_rate': success_rate,
                        'total_uses': len(results)
                    }

        # Sort by savings and return top
        sorted_results = sorted(
            all_results.items(),
            key=lambda x: x[1]['avg_savings_pct'],
            reverse=True
        )

        return [
            {'strategy': name, 'metrics': metrics}
            for name, metrics in sorted_results[:limit]
        ]
