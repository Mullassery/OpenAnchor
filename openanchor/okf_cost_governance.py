"""OKF Cost Governance for OpenAnchor.

Budget enforcement, cost anomaly detection, and spending forecasts
for LLM token consumption across organization.
"""

from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class CostAnomaly:
    """Detected cost anomaly."""

    timestamp: str
    query_cost: float
    expected_cost: float
    deviation_pct: float
    severity: str  # low, medium, high, critical
    reason: str


@dataclass
class BudgetPolicy:
    """Cost budget policy configuration."""

    limit_tokens: int
    enforcement_mode: str  # "hard" (block) or "soft" (warn)
    warning_threshold_pct: float  # e.g., 80%
    lookback_days: int
    reset_frequency: str  # "daily", "weekly", "monthly"


class OKFCostGovernance:
    """Manage cost policies and detect anomalies."""

    def __init__(self, governance_dir: Path = None):
        self.governance_dir = governance_dir or Path.cwd() / "cost_governance"
        self.governance_dir.mkdir(exist_ok=True)
        self.policies: Dict[str, BudgetPolicy] = {}
        self.spending_log: List[Dict] = []

    def set_budget(self, cost_limit: float, enforcement: str = "soft",
                   warning_threshold: float = 80.0) -> None:
        """Set organization-wide budget policy."""
        policy = BudgetPolicy(
            limit_tokens=int(cost_limit),
            enforcement_mode=enforcement,
            warning_threshold_pct=warning_threshold,
            lookback_days=30,
            reset_frequency="monthly"
        )

        with open(self.governance_dir / "budget_policy.json", 'w') as f:
            f.write(json.dumps({
                'limit_tokens': policy.limit_tokens,
                'enforcement_mode': policy.enforcement_mode,
                'warning_threshold_pct': policy.warning_threshold_pct,
                'lookback_days': policy.lookback_days,
                'reset_frequency': policy.reset_frequency,
                'set_at': datetime.now().isoformat()
            }, indent=2))

    def detect_anomaly(self, query_cost: float, domain: str = "default") -> Optional[CostAnomaly]:
        """Detect unusual spending patterns."""
        # Calculate baseline from historical data
        baseline = self._calculate_baseline(domain)
        if not baseline:
            return None

        deviation = ((query_cost - baseline) / baseline) * 100

        if deviation > 50:  # 50% above baseline
            severity = "critical" if deviation > 200 else "high"
            return CostAnomaly(
                timestamp=datetime.now().isoformat(),
                query_cost=query_cost,
                expected_cost=baseline,
                deviation_pct=deviation,
                severity=severity,
                reason=f"Unusual query cost {deviation:.1f}% above baseline"
            )

        return None

    def get_cost_forecast(self, domain: str = "default", days: int = 7) -> Optional[float]:
        """Predict cost from historical patterns."""
        historical = self._get_historical_costs(domain, days=30)
        if not historical:
            return None

        # Simple linear trend
        avg_daily = sum(historical) / len(historical)
        return avg_daily * days

    def record_spend(self, cost: float, model: str, domain: str = "default") -> None:
        """Record spending transaction."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'cost': cost,
            'model': model,
            'domain': domain
        }

        self.spending_log.append(entry)

        # Save to file
        log_file = self.governance_dir / f"spending_{domain}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def _calculate_baseline(self, domain: str) -> Optional[float]:
        """Calculate spending baseline for domain."""
        costs = self._get_historical_costs(domain, days=30)
        if not costs:
            return None

        # Return median (robust to outliers)
        sorted_costs = sorted(costs)
        return sorted_costs[len(sorted_costs) // 2]

    def _get_historical_costs(self, domain: str, days: int = 30) -> List[float]:
        """Retrieve historical costs from log."""
        log_file = self.governance_dir / f"spending_{domain}.jsonl"
        if not log_file.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        costs = []

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry['timestamp'])
                if ts >= cutoff:
                    costs.append(entry['cost'])

        return costs
