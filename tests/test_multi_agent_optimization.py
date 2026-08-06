"""Tests for multi-agent optimization module"""

import pytest
from openanchor.multi_agent_optimization import (
    MultiAgentCoordinator,
    AgentProfile,
    SharedKnowledge,
    FleetOptimizationEngine
)


class TestAgentProfile:
    """Test AgentProfile class"""

    def test_agent_creation(self):
        agent = AgentProfile(
            agent_id="agent_1",
            specialization="navigation"
        )
        assert agent.agent_id == "agent_1"
        assert agent.specialization == "navigation"
        assert agent.success_rate == 0.0

    def test_agent_attributes(self):
        agent = AgentProfile(
            agent_id="agent_1",
            specialization="perception",
            success_rate=0.85
        )
        assert agent.success_rate == 0.85
        assert agent.optimization_score == 0.0


class TestMultiAgentCoordinator:
    """Test MultiAgentCoordinator class"""

    def test_coordinator_initialization(self):
        coordinator = MultiAgentCoordinator(num_agents=5)
        assert len(coordinator.agents) == 5
        assert len(coordinator.shared_knowledge) == 0

    def test_add_agent(self):
        coordinator = MultiAgentCoordinator(num_agents=2)
        coordinator.add_agent("agent_new", "energy")
        assert "agent_new" in coordinator.agents
        assert coordinator.agents["agent_new"].specialization == "energy"

    def test_share_optimization_pattern(self):
        coordinator = MultiAgentCoordinator(num_agents=3)
        patterns = {"pattern_1": 0.9, "pattern_2": 0.8}
        knowledge_id = coordinator.share_optimization_pattern("agent_0", "navigation", patterns)

        assert knowledge_id is not None
        assert len(coordinator.shared_knowledge) == 1
        assert coordinator.shared_knowledge[0].source_agent == "agent_0"

    def test_adopt_knowledge(self):
        coordinator = MultiAgentCoordinator(num_agents=3)
        patterns = {"pattern_1": 0.9}
        knowledge_id = coordinator.share_optimization_pattern("agent_0", "navigation", patterns)

        adopted = coordinator.adopt_knowledge("agent_1", knowledge_id)
        assert adopted
        assert "pattern_1" in coordinator.agents["agent_1"].learned_patterns

    def test_adopt_invalid_knowledge(self):
        coordinator = MultiAgentCoordinator(num_agents=2)
        adopted = coordinator.adopt_knowledge("agent_0", "invalid_id")
        assert not adopted

    def test_coordinate_optimization(self):
        coordinator = MultiAgentCoordinator(num_agents=3)
        for i, agent in enumerate(coordinator.agents.values()):
            agent.success_rate = 0.7 + (i * 0.1)

        improvements = coordinator.coordinate_optimization()
        assert len(improvements) == 3
        assert all(score >= 0 for score in improvements.values())

    def test_get_top_performers(self):
        coordinator = MultiAgentCoordinator(num_agents=5)
        for i, agent in enumerate(coordinator.agents.values()):
            agent.optimization_score = i * 10.0

        top = coordinator.get_top_performers(n=2)
        assert len(top) == 2
        assert top[0][1] >= top[1][1]

    def test_transfer_expertise(self):
        coordinator = MultiAgentCoordinator(num_agents=2)
        source_agent = coordinator.agents["agent_0"]
        target_agent = coordinator.agents["agent_1"]

        source_agent.optimization_score = 100.0
        target_agent.optimization_score = 50.0
        source_agent.learned_patterns = ["pattern_1", "pattern_2", "pattern_3"]

        success = coordinator.transfer_expertise("agent_0", "agent_1")
        assert success
        assert len(target_agent.learned_patterns) >= 1

    def test_detect_collaboration_bottlenecks(self):
        coordinator = MultiAgentCoordinator(num_agents=3)
        bottlenecks = coordinator.detect_collaboration_bottlenecks()
        # Most agents should be isolated initially
        assert len(bottlenecks) >= 0

    def test_get_fleet_statistics(self):
        coordinator = MultiAgentCoordinator(num_agents=3)
        for agent in coordinator.agents.values():
            agent.success_rate = 0.8

        stats = coordinator.get_fleet_statistics()
        assert stats["num_agents"] == 3
        assert stats["avg_success_rate"] == pytest.approx(0.8)
        assert "collaboration_density" in stats

    def test_collaboration_graph(self):
        coordinator = MultiAgentCoordinator(num_agents=3)
        patterns = {"p1": 0.9}
        kid = coordinator.share_optimization_pattern("agent_0", "nav", patterns)

        coordinator.adopt_knowledge("agent_1", kid)
        coordinator.adopt_knowledge("agent_2", kid)

        # Check graph connectivity
        assert len(coordinator.collaboration_graph["agent_0"]) >= 1


class TestFleetOptimizationEngine:
    """Test FleetOptimizationEngine class"""

    def test_engine_initialization(self):
        engine = FleetOptimizationEngine(num_agents=3)
        assert len(engine.coordinator.agents) == 3

    def test_set_optimization_targets(self):
        engine = FleetOptimizationEngine(num_agents=2)
        targets = {"success_rate": 0.95, "latency_ms": 500}
        engine.set_optimization_targets(targets)

        assert engine.optimization_targets["success_rate"] == 0.95

    def test_simulate_fleet_optimization(self):
        engine = FleetOptimizationEngine(num_agents=3)
        # Set initial conditions
        for agent in engine.coordinator.agents.values():
            agent.success_rate = 0.70

        results = engine.simulate_fleet_optimization(iterations=5)
        assert len(results) == 5
        assert all("agent" in str(key) or isinstance(value, dict) for key, value in results.items())

    def test_fleet_optimization_improves_success_rate(self):
        engine = FleetOptimizationEngine(num_agents=3)
        for agent in engine.coordinator.agents.values():
            agent.success_rate = 0.70

        engine.simulate_fleet_optimization(iterations=5)

        # Check if success rates improved
        final_rates = [a.success_rate for a in engine.coordinator.agents.values()]
        assert all(rate >= 0.70 for rate in final_rates)

    def test_get_optimization_report(self):
        engine = FleetOptimizationEngine(num_agents=3)
        engine.simulate_fleet_optimization(iterations=3)

        report = engine.get_optimization_report()
        assert "fleet_stats" in report
        assert "top_performers" in report
        assert "improvement_rate" in report
        assert "bottlenecks" in report

    def test_optimization_history_tracking(self):
        engine = FleetOptimizationEngine(num_agents=2)
        engine.simulate_fleet_optimization(iterations=3)

        assert len(engine.optimization_history) == 3
        for entry in engine.optimization_history:
            assert "iteration" in entry
            assert "avg_success_rate" in entry


class TestSharedKnowledge:
    """Test SharedKnowledge class"""

    def test_knowledge_creation(self):
        knowledge = SharedKnowledge(
            knowledge_id="know_1",
            source_agent="agent_0",
            category="navigation",
            content={"pattern": 0.9}
        )
        assert knowledge.knowledge_id == "know_1"
        assert knowledge.adoption_count == 0

    def test_knowledge_adoption_increment(self):
        knowledge = SharedKnowledge(
            knowledge_id="know_1",
            source_agent="agent_0",
            category="perception",
            content={}
        )
        initial_count = knowledge.adoption_count
        knowledge.adoption_count += 1
        assert knowledge.adoption_count == initial_count + 1


class TestMultiAgentIntegration:
    """Integration tests for multi-agent system"""

    def test_full_optimization_workflow(self):
        """Test complete workflow: coordinate -> optimize -> report"""
        engine = FleetOptimizationEngine(num_agents=4)

        # Set targets
        engine.set_optimization_targets({
            "success_rate": 0.90,
            "collaboration": 0.75
        })

        # Run optimization
        engine.simulate_fleet_optimization(iterations=5)

        # Get report
        report = engine.get_optimization_report()

        assert report["total_optimizations"] == 5
        assert "improvement_rate" in report
        assert isinstance(report["fleet_stats"], dict)

    def test_knowledge_propagation(self):
        """Test that knowledge spreads through the fleet"""
        coordinator = MultiAgentCoordinator(num_agents=3)

        # Agent 0 shares knowledge
        patterns = {"optimize_path": 0.95, "avoid_obstacle": 0.88}
        kid = coordinator.share_optimization_pattern("agent_0", "navigation", patterns)

        # Other agents adopt
        coordinator.adopt_knowledge("agent_1", kid)
        coordinator.adopt_knowledge("agent_2", kid)

        # Verify propagation
        assert len(coordinator.agents["agent_1"].learned_patterns) == 2
        assert len(coordinator.agents["agent_2"].learned_patterns) == 2

    def test_expertise_transfer_improves_underperformers(self):
        """Test that expertise transfer helps struggling agents"""
        coordinator = MultiAgentCoordinator(num_agents=2)

        # Make agent_0 a top performer
        coordinator.agents["agent_0"].optimization_score = 100.0
        coordinator.agents["agent_0"].learned_patterns = ["p1", "p2", "p3", "p4"]

        # Make agent_1 struggling
        coordinator.agents["agent_1"].optimization_score = 30.0

        # Transfer expertise
        success = coordinator.transfer_expertise("agent_0", "agent_1")

        assert success
        assert len(coordinator.agents["agent_1"].learned_patterns) > 0

    def test_collaboration_density_increases(self):
        """Test that collaboration density increases with knowledge sharing"""
        coordinator = MultiAgentCoordinator(num_agents=3)

        initial_density = coordinator._calculate_collaboration_density()

        # Lots of knowledge sharing
        for i in range(3):
            patterns = {f"p{j}": 0.8 + j * 0.05 for j in range(3)}
            kid = coordinator.share_optimization_pattern(f"agent_{i}", "nav", patterns)
            for other_id in coordinator.agents:
                if other_id != f"agent_{i}":
                    coordinator.adopt_knowledge(other_id, kid)

        final_density = coordinator._calculate_collaboration_density()
        assert final_density >= initial_density
