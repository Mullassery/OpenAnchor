"""Tests for federated learning module"""

from openanchor.federated_learning import (
    AggregatedModel,
    FederatedLearner,
    FederatedOptimizer,
    GradientUpdate,
    LocalModel,
)


class TestGradientUpdate:
    """Test GradientUpdate class"""

    def test_gradient_update_creation(self):
        update = GradientUpdate(
            agent_id="agent_1",
            model_version=1,
            gradients={"layer_1": 0.01},
            loss=0.5
        )
        assert update.agent_id == "agent_1"
        assert update.loss == 0.5
        assert update.weight == 1.0

    def test_gradient_update_attributes(self):
        update = GradientUpdate(
            agent_id="agent_1",
            model_version=2,
            gradients={"layer_1": 0.05, "layer_2": -0.02},
            loss=0.3,
            weight=0.5
        )
        assert len(update.gradients) == 2
        assert update.weight == 0.5


class TestAggregatedModel:
    """Test AggregatedModel class"""

    def test_aggregated_model_creation(self):
        model = AggregatedModel(
            model_id="global_v1",
            version=1,
            parameters={"layer_1": 0.5}
        )
        assert model.model_id == "global_v1"
        assert model.version == 1
        assert model.accuracy == 0.0

    def test_aggregated_model_convergence(self):
        model = AggregatedModel(
            model_id="global_v1",
            version=5,
            parameters={},
            convergence_score=0.85
        )
        assert model.convergence_score == 0.85


class TestLocalModel:
    """Test LocalModel class"""

    def test_local_model_creation(self):
        model = LocalModel(agent_id="agent_1")
        assert model.agent_id == "agent_1"
        assert "layer_1" in model.parameters

    def test_local_model_update_from_global(self):
        local = LocalModel(agent_id="agent_1")
        global_params = {"layer_1": 0.6, "layer_2": 0.4}
        local.update_from_global(global_params)

        assert local.parameters == global_params

    def test_local_accuracy(self):
        model = LocalModel(agent_id="agent_1")
        acc = model.local_accuracy()
        assert 0.0 <= acc <= 1.0


class TestFederatedLearner:
    """Test FederatedLearner class"""

    def test_learner_initialization(self):
        learner = FederatedLearner(num_agents=3)
        assert len(learner.agents) == 3
        assert learner.global_model.version == 1

    def test_compute_local_gradients(self):
        learner = FederatedLearner(num_agents=2)
        training_data = {"target_layer_1": 0.7, "target_layer_2": 0.5}

        update = learner.compute_local_gradients("agent_0", training_data)
        assert update is not None
        assert update.agent_id == "agent_0"
        assert update.loss > 0.0

    def test_aggregate_gradients(self):
        learner = FederatedLearner(num_agents=2)

        updates = [
            GradientUpdate("a1", 1, {"layer_1": 0.01}, 0.5, weight=0.5),
            GradientUpdate("a2", 1, {"layer_1": 0.02}, 0.4, weight=0.5),
        ]

        aggregated = learner.aggregate_gradients(updates)
        assert "layer_1" in aggregated

    def test_update_global_model(self):
        learner = FederatedLearner(num_agents=2)

        updates = [
            GradientUpdate("a1", 1, {"layer_1": 0.01, "layer_2": 0.005}, 0.5),
            GradientUpdate("a2", 1, {"layer_1": 0.02, "layer_2": 0.008}, 0.4),
        ]

        initial_version = learner.global_model.version
        learner.update_global_model(updates)

        assert learner.global_model.version > initial_version
        assert learner.global_model.accuracy > 0.0

    def test_broadcast_global_model(self):
        learner = FederatedLearner(num_agents=2)
        learner.global_model.parameters = {"layer_1": 0.6, "layer_2": 0.4}

        learner.broadcast_global_model()

        for agent in learner.agents.values():
            assert agent.parameters == learner.global_model.parameters

    def test_federated_training_round(self):
        learner = FederatedLearner(num_agents=2)

        training_data = {
            "agent_0": {"target_layer_1": 0.7, "target_layer_2": 0.5},
            "agent_1": {"target_layer_1": 0.65, "target_layer_2": 0.55},
        }

        result = learner.federated_training_round(training_data)

        assert "round" in result
        assert "accuracy" in result
        assert "agents_trained" in result

    def test_get_model_drift(self):
        learner = FederatedLearner(num_agents=2)
        learner.agents["agent_0"].parameters = {"layer_1": 0.5, "layer_2": 0.3}
        learner.global_model.parameters = {"layer_1": 0.6, "layer_2": 0.4}

        drift = learner.get_model_drift("agent_0")
        assert drift > 0.0

    def test_calculate_convergence(self):
        learner = FederatedLearner(num_agents=2)

        for i in range(5):
            updates = [
                GradientUpdate("a1", i, {"layer_1": 0.01}, 0.5 - i * 0.05),
                GradientUpdate("a2", i, {"layer_1": 0.02}, 0.4 - i * 0.04),
            ]
            learner.update_global_model(updates)

        convergence = learner._calculate_convergence()
        assert 0.0 <= convergence <= 1.0

    def test_get_fleet_statistics(self):
        learner = FederatedLearner(num_agents=3)

        training_data = {
            "agent_0": {"target_layer_1": 0.7, "target_layer_2": 0.5},
            "agent_1": {"target_layer_1": 0.65, "target_layer_2": 0.55},
            "agent_2": {"target_layer_1": 0.72, "target_layer_2": 0.48},
        }

        learner.federated_training_round(training_data)
        stats = learner.get_fleet_statistics()

        assert "global_accuracy" in stats
        assert "convergence_score" in stats
        assert "avg_model_drift" in stats


class TestFederatedOptimizer:
    """Test FederatedOptimizer class"""

    def test_optimizer_initialization(self):
        optimizer = FederatedOptimizer()
        assert len(optimizer.learning_rate_history) == 0

    def test_calculate_communication_cost(self):
        optimizer = FederatedOptimizer()
        cost = optimizer.calculate_communication_cost(
            num_agents=10,
            num_params=100,
            rounds=5
        )
        assert cost > 0

    def test_adaptive_learning_rate(self):
        optimizer = FederatedOptimizer()
        lr1 = optimizer.adaptive_learning_rate(1, convergence=0.0)
        lr2 = optimizer.adaptive_learning_rate(2, convergence=0.5)

        assert lr1 > lr2  # LR decreases with convergence

    def test_get_optimization_report(self):
        optimizer = FederatedOptimizer()
        optimizer.adaptive_learning_rate(1, 0.1)
        optimizer.adaptive_learning_rate(2, 0.2)

        report = optimizer.get_optimization_report()
        assert "initial_learning_rate" in report
        assert "final_learning_rate" in report
        assert "total_rounds" in report


class TestFederatedLearningIntegration:
    """Integration tests for federated learning"""

    def test_full_training_workflow(self):
        """Test complete federated training loop"""
        learner = FederatedLearner(num_agents=4)

        initial_accuracy = learner.global_model.accuracy

        # Simulate multiple training rounds
        for round_num in range(5):
            training_data = {
                f"agent_{i}": {
                    "target_layer_1": 0.7 + i * 0.02,
                    "target_layer_2": 0.5 + i * 0.01
                }
                for i in range(4)
            }

            result = learner.federated_training_round(training_data)
            assert result["round"] == round_num + 2  # Version starts at 1

        final_accuracy = learner.global_model.accuracy
        # Model should improve (lower loss = higher accuracy)
        assert final_accuracy >= initial_accuracy

    def test_convergence_over_rounds(self):
        """Test that model converges over training"""
        learner = FederatedLearner(num_agents=3)

        convergence_scores = []

        for round_num in range(10):
            training_data = {
                f"agent_{i}": {
                    "target_layer_1": 0.75,
                    "target_layer_2": 0.50
                }
                for i in range(3)
            }

            learner.federated_training_round(training_data)
            convergence_scores.append(learner.global_model.convergence_score)

        # Convergence should generally improve
        assert convergence_scores[-1] >= convergence_scores[0] or len(convergence_scores) == 1

    def test_heterogeneous_data(self):
        """Test learning with heterogeneous (non-IID) data"""
        learner = FederatedLearner(num_agents=4)

        # Each agent has different data distribution
        training_data = {
            "agent_0": {"target_layer_1": 0.9, "target_layer_2": 0.1},
            "agent_1": {"target_layer_1": 0.8, "target_layer_2": 0.2},
            "agent_2": {"target_layer_1": 0.7, "target_layer_2": 0.3},
            "agent_3": {"target_layer_1": 0.6, "target_layer_2": 0.4},
        }

        result = learner.federated_training_round(training_data)

        # Should still converge despite non-IID data
        assert result["accuracy"] >= 0.0
        assert result["agents_trained"] == 4

    def test_agent_dropout_resilience(self):
        """Test that system handles agent dropout gracefully"""
        learner = FederatedLearner(num_agents=5)

        # First round: all agents
        training_data_1 = {
            f"agent_{i}": {"target_layer_1": 0.7, "target_layer_2": 0.5}
            for i in range(5)
        }
        learner.federated_training_round(training_data_1)

        # Second round: only 3 agents (2 dropped)
        training_data_2 = {
            f"agent_{i}": {"target_layer_1": 0.7, "target_layer_2": 0.5}
            for i in range(3)
        }
        result = learner.federated_training_round(training_data_2)

        # Should still work with fewer agents
        assert result["agents_trained"] == 3
        assert result["accuracy"] > 0.0

    def test_model_personalization(self):
        """Test that agents can specialize with federated learning"""
        learner = FederatedLearner(num_agents=2)

        # Agent 0 specializes in high layer_1 values
        # Agent 1 specializes in high layer_2 values
        training_data = {
            "agent_0": {"target_layer_1": 0.95, "target_layer_2": 0.1},
            "agent_1": {"target_layer_1": 0.1, "target_layer_2": 0.95},
        }

        learner.federated_training_round(training_data)

        # Global model should balance both specializations
        global_params = learner.global_model.parameters
        assert 0.3 < global_params.get("layer_1", 0) < 0.7
        assert 0.3 < global_params.get("layer_2", 0) < 0.7
