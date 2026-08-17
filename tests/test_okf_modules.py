"""Tests for openanchor/okf_*.py modules (cost governance, token profiles,
optimization tracking). All three previously had zero test coverage.
"""

import pytest

from openanchor.okf_cost_governance import BudgetPolicy, OKFCostGovernance
from openanchor.okf_optimization_tracking import (
    OKFOptimizationTracking,
    OptimizationLeaderboard,
)
from openanchor.okf_token_profiles import (
    OKFTokenProfileCatalog,
    TokenProfile,
    TokenProfileAnalyzer,
)


class TestOKFCostGovernance:
    @pytest.fixture
    def governance(self, tmp_path):
        return OKFCostGovernance(governance_dir=tmp_path / "gov")

    def test_governance_dir_created(self, governance, tmp_path):
        assert (tmp_path / "gov").exists()

    def test_set_budget_writes_policy_file(self, governance, tmp_path):
        governance.set_budget(cost_limit=1000, enforcement="hard", warning_threshold=90.0)
        policy_file = tmp_path / "gov" / "budget_policy.json"
        assert policy_file.exists()
        import json

        data = json.loads(policy_file.read_text())
        assert data["limit_tokens"] == 1000
        assert data["enforcement_mode"] == "hard"

    def test_record_spend_and_forecast(self, governance):
        governance.record_spend(cost=10.0, model="gpt-4", domain="default")
        governance.record_spend(cost=12.0, model="gpt-4", domain="default")
        forecast = governance.get_cost_forecast(domain="default", days=7)
        assert forecast is not None
        assert forecast > 0

    def test_forecast_none_without_history(self, governance):
        assert governance.get_cost_forecast(domain="empty_domain") is None

    def test_detect_anomaly_flags_spike(self, governance):
        for _ in range(5):
            governance.record_spend(cost=10.0, model="gpt-4", domain="d")
        anomaly = governance.detect_anomaly(query_cost=100.0, domain="d")
        assert anomaly is not None
        assert anomaly.severity in ("high", "critical")

    def test_detect_anomaly_none_for_normal_spend(self, governance):
        for _ in range(5):
            governance.record_spend(cost=10.0, model="gpt-4", domain="d2")
        anomaly = governance.detect_anomaly(query_cost=10.5, domain="d2")
        assert anomaly is None

    def test_detect_anomaly_none_without_baseline(self, governance):
        assert governance.detect_anomaly(query_cost=100.0, domain="no_history") is None


class TestBudgetPolicy:
    def test_construction(self):
        policy = BudgetPolicy(
            limit_tokens=1000,
            enforcement_mode="soft",
            warning_threshold_pct=80.0,
            lookback_days=30,
            reset_frequency="monthly",
        )
        assert policy.limit_tokens == 1000


class TestOKFTokenProfileCatalog:
    @pytest.fixture
    def catalog(self, tmp_path):
        return OKFTokenProfileCatalog(catalog_dir=tmp_path / "profiles")

    def test_save_and_get_profile(self, catalog):
        profile = TokenProfile(
            model_id="gpt-4",
            domain="support",
            system_prompt_pct=10.0,
            retrieval_pct=30.0,
            user_input_pct=50.0,
            overhead_pct=10.0,
            avg_total_tokens=1500,
            percentile_95=3000,
            samples=100,
            last_updated="2026-01-01",
        )
        catalog.save_profile(profile)
        fetched = catalog.get_profile("gpt-4", "support")
        assert fetched is not None
        assert fetched.avg_total_tokens == 1500

    def test_get_profile_missing_returns_none(self, catalog):
        assert catalog.get_profile("nonexistent", "domain") is None

    def test_get_model_efficiency(self, catalog):
        catalog.save_profile(TokenProfile(
            model_id="gpt-4", domain="a", system_prompt_pct=0, retrieval_pct=0,
            user_input_pct=0, overhead_pct=0, avg_total_tokens=1000, percentile_95=2000,
            samples=10, last_updated="2026-01-01",
        ))
        catalog.save_profile(TokenProfile(
            model_id="gpt-4", domain="b", system_prompt_pct=0, retrieval_pct=0,
            user_input_pct=0, overhead_pct=0, avg_total_tokens=2000, percentile_95=3000,
            samples=10, last_updated="2026-01-01",
        ))
        efficiency = catalog.get_model_efficiency(["gpt-4"])
        assert efficiency["gpt-4"] == 1500.0


class TestTokenProfileAnalyzer:
    @pytest.fixture
    def catalog(self, tmp_path):
        return OKFTokenProfileCatalog(catalog_dir=tmp_path / "profiles")

    def test_estimate_cost(self, catalog):
        catalog.save_profile(TokenProfile(
            model_id="gpt-4", domain="support",
            system_prompt_pct=10.0, retrieval_pct=20.0, user_input_pct=60.0, overhead_pct=10.0,
            avg_total_tokens=1000, percentile_95=2000, samples=10, last_updated="2026-01-01",
        ))
        total = TokenProfileAnalyzer.estimate_cost("gpt-4", "support", 100, catalog)
        assert total == 100 + 10 + 20 + 10  # system+input+retrieval+overhead tokens

    def test_estimate_cost_none_without_profile(self, catalog):
        assert TokenProfileAnalyzer.estimate_cost("gpt-4", "missing", 100, catalog) is None

    def test_recommend_model_picks_lowest_average(self, catalog):
        catalog.save_profile(TokenProfile(
            model_id="gpt-4", domain="support", system_prompt_pct=0, retrieval_pct=0,
            user_input_pct=0, overhead_pct=0, avg_total_tokens=5000, percentile_95=6000,
            samples=10, last_updated="2026-01-01",
        ))
        catalog.save_profile(TokenProfile(
            model_id="gpt-3.5", domain="support", system_prompt_pct=0, retrieval_pct=0,
            user_input_pct=0, overhead_pct=0, avg_total_tokens=2000, percentile_95=3000,
            samples=10, last_updated="2026-01-01",
        ))
        best = TokenProfileAnalyzer.recommend_model("support", budget=10000, catalog=catalog)
        assert best == "gpt-3.5"

    def test_recommend_model_none_when_over_budget(self, catalog):
        catalog.save_profile(TokenProfile(
            model_id="gpt-4", domain="support", system_prompt_pct=0, retrieval_pct=0,
            user_input_pct=0, overhead_pct=0, avg_total_tokens=5000, percentile_95=6000,
            samples=10, last_updated="2026-01-01",
        ))
        assert TokenProfileAnalyzer.recommend_model("support", budget=100, catalog=catalog) is None


class TestOKFOptimizationTracking:
    @pytest.fixture
    def tracker(self, tmp_path):
        return OKFOptimizationTracking(tracking_dir=tmp_path / "tracking")

    def test_record_and_get_effectiveness(self, tracker):
        tracker.record_optimization(
            strategy="prompt_compression", baseline_cost=10.0, optimized_cost=6.0,
            success=True, model="gpt-4", domain="default",
        )
        tracker.record_optimization(
            strategy="prompt_compression", baseline_cost=10.0, optimized_cost=8.0,
            success=False, model="gpt-4", domain="default",
        )
        effectiveness = tracker.get_strategy_effectiveness("prompt_compression")
        assert effectiveness["total_trials"] == 2
        assert effectiveness["success_rate"] == 50.0

    def test_effectiveness_empty_for_unknown_strategy(self, tracker):
        effectiveness = tracker.get_strategy_effectiveness("never_used")
        assert effectiveness["total_trials"] == 0
        assert effectiveness["success_rate"] == 0.0

    def test_recommend_optimizations(self, tracker):
        tracker.record_optimization(
            strategy="caching", baseline_cost=10.0, optimized_cost=2.0,
            success=True, model="gpt-4", domain="support",
        )
        tracker.record_optimization(
            strategy="compression", baseline_cost=10.0, optimized_cost=8.0,
            success=True, model="gpt-4", domain="support",
        )
        recommendations = tracker.recommend_optimizations("gpt-4", domain="support", top_n=2)
        assert len(recommendations) == 2
        assert recommendations[0]["strategy"] == "caching"  # bigger reduction first

    def test_reduction_pct_computed_correctly(self, tracker):
        tracker.record_optimization(
            strategy="s", baseline_cost=100.0, optimized_cost=75.0,
            success=True, model="m", domain="d",
        )
        effectiveness = tracker.get_strategy_effectiveness("s")
        assert effectiveness["avg_savings"] == pytest.approx(25.0)


class TestOptimizationLeaderboard:
    def test_get_best_strategies(self, tmp_path):
        tracker = OKFOptimizationTracking(tracking_dir=tmp_path / "tracking")
        tracker.record_optimization(
            strategy="big_win", baseline_cost=10.0, optimized_cost=1.0,
            success=True, model="m", domain="d",
        )
        tracker.record_optimization(
            strategy="small_win", baseline_cost=10.0, optimized_cost=9.0,
            success=True, model="m", domain="d",
        )
        leaderboard = OptimizationLeaderboard(tracking_dir=tmp_path / "tracking")
        best = leaderboard.get_best_strategies(limit=5)
        assert best[0]["strategy"] == "big_win"

    def test_empty_leaderboard(self, tmp_path):
        leaderboard = OptimizationLeaderboard(tracking_dir=tmp_path / "empty")
        assert leaderboard.get_best_strategies() == []
