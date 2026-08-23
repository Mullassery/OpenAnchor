"""Multi-agent Optimization - Coordinate agents for fleet-wide improvements

OpenAnchor Phase 3: Enable multiple agents to share knowledge, coordinate optimization
efforts, and learn collaboratively from each other's experiences.
"""

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class AgentProfile:
    """Profile of an agent in the fleet"""
    agent_id: str
    specialization: str  # "navigation", "perception", "energy", etc.
    success_rate: float = 0.0
    cached_tokens: int = 0
    learned_patterns: List[str] = field(default_factory=list)
    optimization_score: float = 0.0


@dataclass
class SharedKnowledge:
    """Knowledge shared between agents"""
    knowledge_id: str
    source_agent: str
    category: str
    content: Dict[str, float]  # Pattern -> effectiveness score
    timestamp: int = 0
    relevance_score: float = 0.0
    adoption_count: int = 0


class MultiAgentCoordinator:
    """Coordinate multiple agents for collaborative learning"""

    def __init__(self, num_agents: int = 5):
        self.agents: Dict[str, AgentProfile] = {}
        self.shared_knowledge: List[SharedKnowledge] = []
        self.collaboration_graph: Dict[str, Set[str]] = defaultdict(set)
        self.optimization_log: List[Dict] = []
        self._initialize_agents(num_agents)

    def _initialize_agents(self, num_agents: int):
        """Initialize agent profiles"""
        specializations = ["navigation", "perception", "energy", "control", "planning"]
        for i in range(num_agents):
            spec = specializations[i % len(specializations)]
            agent = AgentProfile(
                agent_id=f"agent_{i}",
                specialization=spec
            )
            self.agents[agent.agent_id] = agent

    def add_agent(self, agent_id: str, specialization: str):
        """Add new agent to the fleet"""
        agent = AgentProfile(
            agent_id=agent_id,
            specialization=specialization
        )
        self.agents[agent_id] = agent

    def share_optimization_pattern(self, source_agent: str, category: str,
                                   patterns: Dict[str, float]) -> str:
        """Agent shares learned optimization patterns with fleet"""
        knowledge_id = hashlib.md5(
            f"{source_agent}_{category}_{len(self.shared_knowledge)}".encode(),
            usedforsecurity=False,
        ).hexdigest()[:12]

        relevance = self._calculate_pattern_relevance(category, patterns)
        knowledge = SharedKnowledge(
            knowledge_id=knowledge_id,
            source_agent=source_agent,
            category=category,
            content=patterns,
            relevance_score=relevance
        )

        self.shared_knowledge.append(knowledge)
        return knowledge_id

    def _calculate_pattern_relevance(self, category: str, patterns: Dict[str, float]) -> float:
        """Calculate relevance of patterns (higher effectiveness = higher relevance)"""
        if not patterns:
            return 0.0
        avg_effectiveness = sum(patterns.values()) / len(patterns)
        return min(avg_effectiveness, 1.0)

    def adopt_knowledge(self, agent_id: str, knowledge_id: str) -> bool:
        """Agent adopts shared knowledge from fleet"""
        if agent_id not in self.agents:
            return False

        knowledge = next((k for k in self.shared_knowledge if k.knowledge_id == knowledge_id), None)
        if not knowledge:
            return False

        agent = self.agents[agent_id]
        agent.learned_patterns.extend(knowledge.content.keys())
        knowledge.adoption_count += 1

        # Record collaboration
        self.collaboration_graph[agent_id].add(knowledge.source_agent)
        self.collaboration_graph[knowledge.source_agent].add(agent_id)

        return True

    def coordinate_optimization(self) -> Dict[str, float]:
        """Coordinate multi-agent optimization across the fleet"""
        fleet_improvements = {}

        for agent_id, agent in self.agents.items():
            # Calculate agent optimization score
            base_score = agent.success_rate * 100.0
            pattern_bonus = len(agent.learned_patterns) * 2.0
            collaboration_bonus = len(self.collaboration_graph[agent_id]) * 3.0

            agent.optimization_score = base_score + pattern_bonus + collaboration_bonus

            fleet_improvements[agent_id] = agent.optimization_score

        # Log coordination event
        self.optimization_log.append({
            "type": "fleet_coordination",
            "agent_scores": fleet_improvements,
            "avg_score": sum(fleet_improvements.values()) / len(fleet_improvements) if fleet_improvements else 0.0
        })

        return fleet_improvements

    def get_top_performers(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N performing agents"""
        scores = [(aid, agent.optimization_score) for aid, agent in self.agents.items()]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]

    def transfer_expertise(self, source_agent: str, target_agent: str) -> bool:
        """Transfer expertise from high performer to struggling agent"""
        if source_agent not in self.agents or target_agent not in self.agents:
            return False

        source = self.agents[source_agent]
        target = self.agents[target_agent]

        # Only transfer if source is actually better
        if source.optimization_score <= target.optimization_score:
            return False

        # Transfer some learned patterns
        patterns_to_transfer = source.learned_patterns[:len(source.learned_patterns) // 2]
        target.learned_patterns.extend(patterns_to_transfer)

        # Record transfer
        self.optimization_log.append({
            "type": "expertise_transfer",
            "source": source_agent,
            "target": target_agent,
            "patterns_transferred": len(patterns_to_transfer)
        })

        return True

    def detect_collaboration_bottlenecks(self) -> List[str]:
        """Identify agents that are isolated or under-collaborating"""
        bottlenecks = []
        avg_collaborations = sum(len(neighbors) for neighbors in self.collaboration_graph.values()) / max(len(self.agents), 1)

        for agent_id in self.agents:
            if len(self.collaboration_graph[agent_id]) < avg_collaborations / 2:
                bottlenecks.append(agent_id)

        return bottlenecks

    def get_fleet_statistics(self) -> Dict[str, float]:
        """Get overall fleet statistics"""
        agent_list = list(self.agents.values())

        stats = {
            "num_agents": len(agent_list),
            "avg_success_rate": sum(a.success_rate for a in agent_list) / len(agent_list) if agent_list else 0.0,
            "total_shared_knowledge": len(self.shared_knowledge),
            "avg_patterns_per_agent": sum(len(a.learned_patterns) for a in agent_list) / len(agent_list) if agent_list else 0.0,
            "collaboration_density": self._calculate_collaboration_density(),
        }

        return stats

    def _calculate_collaboration_density(self) -> float:
        """Calculate network collaboration density (0-1)"""
        if len(self.agents) < 2:
            return 0.0

        total_edges = sum(len(neighbors) for neighbors in self.collaboration_graph.values()) / 2
        max_edges = len(self.agents) * (len(self.agents) - 1) / 2

        return total_edges / max_edges if max_edges > 0 else 0.0


class FleetOptimizationEngine:
    """Fleet-wide optimization using multi-agent coordination"""

    def __init__(self, num_agents: int = 5):
        self.coordinator = MultiAgentCoordinator(num_agents)
        self.optimization_targets: Dict[str, float] = {}
        self.optimization_history: List[Dict] = []

    def set_optimization_targets(self, targets: Dict[str, float]):
        """Set targets for fleet optimization (e.g., success_rate: 0.95, latency_ms: 500)"""
        self.optimization_targets = targets

    def simulate_fleet_optimization(self, iterations: int = 10) -> Dict[str, Dict[str, float]]:
        """Simulate multi-iteration fleet optimization"""
        results: Dict[str, Dict[str, float]] = {}

        for iteration in range(iterations):
            # Each agent makes progress
            for agent_id, agent in self.coordinator.agents.items():
                # Success rate improves with learning
                improvement = 0.01 * (1 + len(agent.learned_patterns) / 10.0)
                agent.success_rate = min(agent.success_rate + improvement, 1.0)

            # Coordinate optimization across fleet
            fleet_scores = self.coordinator.coordinate_optimization()

            # Top performers share knowledge
            top_performers = self.coordinator.get_top_performers(2)
            for source_id, _ in top_performers:
                for target_id in self.coordinator.agents:
                    if target_id != source_id and self.coordinator.agents[target_id].success_rate < 0.85:
                        self.coordinator.transfer_expertise(source_id, target_id)

            # Log iteration results
            self.optimization_history.append({
                "iteration": iteration,
                "fleet_scores": fleet_scores,
                "avg_success_rate": sum(a.success_rate for a in self.coordinator.agents.values()) / len(self.coordinator.agents)
            })

            results[f"iter_{iteration}"] = fleet_scores

        return results

    def get_optimization_report(self) -> Dict:
        """Generate comprehensive optimization report"""
        stats = self.coordinator.get_fleet_statistics()
        bottlenecks = self.coordinator.detect_collaboration_bottlenecks()
        top_performers = self.coordinator.get_top_performers(3)

        # Calculate improvement trajectory
        if len(self.optimization_history) >= 2:
            first_iter = self.optimization_history[0]["avg_success_rate"]
            last_iter = self.optimization_history[-1]["avg_success_rate"]
            improvement_rate = (last_iter - first_iter) / max(first_iter, 0.01)
        else:
            improvement_rate = 0.0

        return {
            "fleet_stats": stats,
            "bottlenecks": bottlenecks,
            "top_performers": [(aid, score) for aid, score in top_performers],
            "improvement_rate": improvement_rate,
            "total_optimizations": len(self.optimization_history),
        }
