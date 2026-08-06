"""Tests for model evolution module"""

import pytest
from openanchor.model_evolution import (
    ModelCheckpoint,
    ModelEvolutionTracker,
    AdaptiveHyperparameterTuner,
    ModelSelector,
    GridSearchOptimizer,
)


class TestModelEvolutionTracker:
    """Test model evolution tracking"""

    def test_tracker_creation(self):
        tracker = ModelEvolutionTracker()
        assert len(tracker.checkpoints) == 0

    def test_add_checkpoint(self):
        tracker = ModelEvolutionTracker()
        cp = ModelCheckpoint("cp1", 1, 0.85, 0.15, 0.01, {})
        tracker.add_checkpoint(cp)
        assert len(tracker.checkpoints) == 1

    def test_best_checkpoint_tracking(self):
        tracker = ModelEvolutionTracker()
        cp1 = ModelCheckpoint("cp1", 1, 0.80, 0.20, 0.01, {})
        cp2 = ModelCheckpoint("cp2", 2, 0.90, 0.10, 0.01, {})

        tracker.add_checkpoint(cp1)
        tracker.add_checkpoint(cp2)

        assert tracker.best_checkpoint.accuracy == 0.90

    def test_improvement_rate(self):
        tracker = ModelEvolutionTracker()
        tracker.add_checkpoint(ModelCheckpoint("cp1", 0, 0.50, 0.50, 0.01, {}))
        tracker.add_checkpoint(ModelCheckpoint("cp2", 10, 0.80, 0.20, 0.01, {}))

        rate = tracker.get_improvement_rate()
        assert rate > 0.0

    def test_plateau_detection(self):
        tracker = ModelEvolutionTracker()
        # Add checkpoints with plateauing accuracy
        for i in range(6):
            acc = 0.85 if i < 3 else 0.851
            tracker.add_checkpoint(ModelCheckpoint(f"cp{i}", i, acc, 0.15, 0.01, {}))

        # Should detect plateau
        assert tracker.has_plateau(window=3)


class TestAdaptiveHyperparameterTuner:
    """Test adaptive tuning"""

    def test_tuner_creation(self):
        tuner = AdaptiveHyperparameterTuner()
        assert "learning_rate" in tuner.current_params

    def test_get_suggestions(self):
        tuner = AdaptiveHyperparameterTuner()
        tracker = ModelEvolutionTracker()

        # Add some checkpoints
        for i in range(5):
            tracker.add_checkpoint(ModelCheckpoint(f"cp{i}", i, 0.50 + i * 0.05, 0.50 - i * 0.05, 0.01, {}))

        suggestions = tuner.get_suggestions(tracker)
        # May or may not get suggestions depending on conditions
        assert isinstance(suggestions, list)

    def test_apply_suggestion(self):
        tuner = AdaptiveHyperparameterTuner()
        from openanchor.model_evolution import HyperparameterSuggestion

        suggestion = HyperparameterSuggestion("learning_rate", 0.01, 0.005, 5.0, 0.7)
        old_lr = tuner.current_params["learning_rate"]
        tuner.apply_suggestion(suggestion)

        assert tuner.current_params["learning_rate"] == 0.005
        assert len(tuner.tuning_history) == 1


class TestModelSelector:
    """Test model selection"""

    def test_selector_creation(self):
        selector = ModelSelector()
        assert len(selector.candidates) == 0

    def test_add_model(self):
        selector = ModelSelector()
        cp = ModelCheckpoint("cp1", 1, 0.85, 0.15, 0.01, {})
        selector.add_model("model1", cp)

        assert len(selector.candidates) == 1

    def test_select_best(self):
        selector = ModelSelector()
        selector.add_model("m1", ModelCheckpoint("cp1", 1, 0.80, 0.20, 0.01, {}))
        selector.add_model("m2", ModelCheckpoint("cp2", 1, 0.90, 0.10, 0.01, {}))

        best_id, best_cp = selector.select_best(metric="accuracy")
        assert best_id == "m2"
        assert best_cp.accuracy == 0.90

    def test_ensemble_weights(self):
        selector = ModelSelector()
        selector.add_model("m1", ModelCheckpoint("cp1", 1, 0.80, 0.20, 0.01, {}))
        selector.add_model("m2", ModelCheckpoint("cp2", 1, 0.90, 0.10, 0.01, {}))

        weights = selector.get_ensemble_weights()
        assert "m1" in weights
        assert "m2" in weights
        assert abs(sum(weights.values()) - 1.0) < 0.01

    def test_selector_statistics(self):
        selector = ModelSelector()
        selector.add_model("m1", ModelCheckpoint("cp1", 1, 0.80, 0.20, 0.01, {}))

        stats = selector.get_statistics()
        assert stats["num_models"] == 1


class TestGridSearchOptimizer:
    """Test grid search optimization"""

    def test_optimizer_creation(self):
        optimizer = GridSearchOptimizer()
        assert len(optimizer.param_grid) == 0

    def test_set_param_grid(self):
        optimizer = GridSearchOptimizer()
        grid = {"lr": [0.001, 0.01, 0.1], "dropout": [0.3, 0.5]}
        optimizer.set_param_grid(grid)

        assert optimizer.get_total_combinations() == 6

    def test_record_result(self):
        optimizer = GridSearchOptimizer()
        params = {"lr": 0.01}
        optimizer.record_result(params, 0.85)

        assert len(optimizer.search_results) == 1

    def test_get_best_params(self):
        optimizer = GridSearchOptimizer()
        optimizer.record_result({"lr": 0.001}, 0.75)
        optimizer.record_result({"lr": 0.01}, 0.85)

        best = optimizer.get_best_params()
        assert best["lr"] == 0.01

    def test_estimate_search_cost(self):
        optimizer = GridSearchOptimizer()
        optimizer.set_param_grid({"lr": [0.001, 0.01], "drop": [0.3, 0.5]})

        cost = optimizer.estimate_search_cost(time_per_eval=10.0)
        assert cost > 0.0


class TestModelEvolutionIntegration:
    """Integration tests"""

    def test_full_workflow(self):
        """Test complete model evolution workflow"""
        tracker = ModelEvolutionTracker()
        tuner = AdaptiveHyperparameterTuner()
        selector = ModelSelector()

        # Simulate training
        for epoch in range(10):
            acc = 0.5 + epoch * 0.04
            cp = ModelCheckpoint(f"cp{epoch}", epoch, acc, 1.0 - acc, 0.01, {})
            tracker.add_checkpoint(cp)
            selector.add_model(f"model_{epoch}", cp)

        # Get suggestions and select best
        suggestions = tuner.get_suggestions(tracker)
        best = selector.select_best()

        assert tracker.best_checkpoint is not None
        assert best is not None
        assert best[1].accuracy > 0.8
