"""Federated Learning - Distributed intelligence across agent fleets

OpenAnchor Phase 4: Enable agents to learn from each other without centralizing data.
Each agent maintains local models and shares gradient updates, not raw data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import hashlib
from collections import defaultdict


@dataclass
class GradientUpdate:
    """Local gradient update from an agent"""
    agent_id: str
    model_version: int
    gradients: Dict[str, float]  # Layer -> gradient value
    loss: float
    timestamp: int = 0
    weight: float = 1.0  # Contribution weight


@dataclass
class AggregatedModel:
    """Fleet-wide aggregated model parameters"""
    model_id: str
    version: int
    parameters: Dict[str, float]  # Layer -> parameter value
    accuracy: float = 0.0
    convergence_score: float = 0.0  # How well converged? (0-1)
    num_agents_trained: int = 0


class FederatedLearner:
    """Coordinate federated learning across agent fleet"""

    def __init__(self, num_agents: int = 5, learning_rate: float = 0.01):
        self.agents: Dict[str, LocalModel] = {}
        self.global_model: AggregatedModel = AggregatedModel(
            model_id="global_v1",
            version=1,
            parameters={}
        )
        self.gradient_history: List[GradientUpdate] = []
        self.learning_rate = learning_rate
        self._initialize_agents(num_agents)

    def _initialize_agents(self, num_agents: int):
        """Initialize local models for each agent"""
        for i in range(num_agents):
            agent_id = f"agent_{i}"
            local_model = LocalModel(
                agent_id=agent_id,
                parameters={"layer_1": 0.5 + i * 0.01, "layer_2": 0.3 + i * 0.005}
            )
            self.agents[agent_id] = local_model

    def compute_local_gradients(self, agent_id: str, training_data: Dict[str, float]) -> GradientUpdate:
        """Agent computes gradients on its local data"""
        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]

        # Simulate gradient computation
        gradients = {}
        loss = 0.0

        for param_name in agent.parameters:
            # Gradient is change needed to improve parameter
            gradient = training_data.get("target_" + param_name, 0.0) - agent.parameters[param_name]
            gradients[param_name] = gradient * 0.1  # Scale down
            loss += abs(gradient)

        loss = loss / max(len(gradients), 1)

        update = GradientUpdate(
            agent_id=agent_id,
            model_version=agent.version,
            gradients=gradients,
            loss=loss,
            weight=1.0 / len(self.agents)  # Equal weight (can be data-dependent)
        )

        self.gradient_history.append(update)
        return update

    def aggregate_gradients(self, gradient_updates: List[GradientUpdate]) -> Dict[str, float]:
        """Aggregate gradients from multiple agents (FedAvg)"""
        if not gradient_updates:
            return {}

        # Weighted average of gradients
        aggregated = defaultdict(float)
        total_weight = sum(u.weight for u in gradient_updates)

        for update in gradient_updates:
            for param_name, gradient in update.gradients.items():
                weighted_gradient = gradient * (update.weight / max(total_weight, 1e-6))
                aggregated[param_name] += weighted_gradient

        return dict(aggregated)

    def update_global_model(self, gradient_updates: List[GradientUpdate]):
        """Apply aggregated gradients to global model"""
        aggregated_grads = self.aggregate_gradients(gradient_updates)

        # Update global model parameters
        if not self.global_model.parameters:
            self.global_model.parameters = {name: 0.5 for name in aggregated_grads}

        for param_name, gradient in aggregated_grads.items():
            if param_name not in self.global_model.parameters:
                self.global_model.parameters[param_name] = 0.5

            # Apply learning rate
            self.global_model.parameters[param_name] += self.learning_rate * gradient

        # Calculate global accuracy (mock)
        avg_loss = sum(u.loss for u in gradient_updates) / len(gradient_updates) if gradient_updates else 0.0
        self.global_model.accuracy = max(0.0, 1.0 - avg_loss)
        self.global_model.version += 1
        self.global_model.num_agents_trained = len(gradient_updates)

    def broadcast_global_model(self):
        """Send updated global model to all agents"""
        for agent in self.agents.values():
            agent.parameters = self.global_model.parameters.copy()
            agent.version = self.global_model.version

    def federated_training_round(self, training_data: Dict[str, Dict[str, float]]) -> Dict:
        """Execute one round of federated learning"""
        gradient_updates = []

        # Local training on each agent
        for agent_id, data in training_data.items():
            if agent_id in self.agents:
                update = self.compute_local_gradients(agent_id, data)
                if update:
                    gradient_updates.append(update)

        # Server-side aggregation and update
        self.update_global_model(gradient_updates)
        self.broadcast_global_model()

        return {
            "round": self.global_model.version,
            "accuracy": self.global_model.accuracy,
            "agents_trained": self.global_model.num_agents_trained,
            "convergence": self._calculate_convergence()
        }

    def _calculate_convergence(self) -> float:
        """Estimate convergence using gradient variance"""
        if len(self.gradient_history) < 2:
            return 0.0

        recent_losses = [u.loss for u in self.gradient_history[-10:]]
        if len(recent_losses) < 2:
            return 0.0

        # Lower variance = better convergence
        avg_loss = sum(recent_losses) / len(recent_losses)
        variance = sum((l - avg_loss) ** 2 for l in recent_losses) / len(recent_losses)

        # Convert variance to convergence score (0-1)
        convergence = max(0.0, 1.0 - variance)
        self.global_model.convergence_score = convergence
        return convergence

    def get_model_drift(self, agent_id: str) -> float:
        """Measure how far local model drifts from global model"""
        if agent_id not in self.agents:
            return 0.0

        agent = self.agents[agent_id]
        drift = 0.0

        for param_name in agent.parameters:
            global_param = self.global_model.parameters.get(param_name, 0.5)
            local_param = agent.parameters.get(param_name, 0.5)
            drift += abs(global_param - local_param)

        return drift / max(len(agent.parameters), 1)

    def get_fleet_statistics(self) -> Dict[str, float]:
        """Get fleet-wide learning statistics"""
        stats = {
            "global_model_version": float(self.global_model.version),
            "global_accuracy": self.global_model.accuracy,
            "convergence_score": self.global_model.convergence_score,
            "avg_model_drift": 0.0,
        }

        if self.agents:
            drifts = [self.get_model_drift(aid) for aid in self.agents]
            stats["avg_model_drift"] = sum(drifts) / len(drifts)
            stats["max_model_drift"] = max(drifts) if drifts else 0.0

        return stats


class LocalModel:
    """Local model on individual agent"""

    def __init__(self, agent_id: str, parameters: Optional[Dict[str, float]] = None):
        self.agent_id = agent_id
        self.parameters = parameters or {"layer_1": 0.5, "layer_2": 0.3}
        self.version = 1
        self.training_count = 0

    def update_from_global(self, global_params: Dict[str, float]):
        """Update local model from global model"""
        self.parameters = global_params.copy()
        self.training_count += 1

    def local_accuracy(self) -> float:
        """Estimate local model accuracy (mock)"""
        return 0.7 + (self.training_count * 0.01)


class FederatedOptimizer:
    """Optimize federated learning parameters"""

    def __init__(self):
        self.learning_rate_history: List[Tuple[int, float]] = []
        self.communication_cost: int = 0

    def calculate_communication_cost(self, num_agents: int, num_params: int, rounds: int) -> int:
        """Estimate communication cost (bytes transferred)"""
        # Each agent sends gradients, server sends updated model
        bytes_per_update = num_params * 4  # 4 bytes per float
        return 2 * num_agents * bytes_per_update * rounds

    def adaptive_learning_rate(self, round_num: int, convergence: float) -> float:
        """Adapt learning rate based on convergence"""
        base_lr = 0.01
        # Decrease LR as convergence improves
        lr = base_lr * (1.0 - convergence * 0.5)
        self.learning_rate_history.append((round_num, lr))
        return lr

    def get_optimization_report(self) -> Dict:
        """Generate optimization report"""
        if not self.learning_rate_history:
            return {}

        lrs = [lr for _, lr in self.learning_rate_history]
        return {
            "initial_learning_rate": lrs[0] if lrs else 0.0,
            "final_learning_rate": lrs[-1] if lrs else 0.0,
            "total_rounds": len(self.learning_rate_history),
            "communication_rounds": len(self.learning_rate_history),
        }
