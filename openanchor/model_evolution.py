"""Model Evolution & Adaptive Hyperparameter Tuning - OpenAnchor Phase 5

Track model performance over time, evolve hyperparameters adaptively,
and select best-performing models for deployment.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ModelCheckpoint:
    """Snapshot of model state at a point in time"""
    checkpoint_id: str
    epoch: int
    accuracy: float
    loss: float
    learning_rate: float
    hyperparameters: Dict[str, float]
    timestamp: int = 0


@dataclass
class HyperparameterSuggestion:
    """Recommended hyperparameter adjustment"""
    param_name: str
    current_value: float
    suggested_value: float
    expected_improvement: float  # % improvement
    confidence: float


class ModelEvolutionTracker:
    """Track model performance and evolution across training"""

    def __init__(self):
        self.checkpoints: List[ModelCheckpoint] = []
        self.best_checkpoint: Optional[ModelCheckpoint] = None
        self.performance_history: List[Tuple[int, float]] = []

    def add_checkpoint(self, checkpoint: ModelCheckpoint):
        """Record model checkpoint"""
        self.checkpoints.append(checkpoint)
        self.performance_history.append((checkpoint.epoch, checkpoint.accuracy))

        if self.best_checkpoint is None or checkpoint.accuracy > self.best_checkpoint.accuracy:
            self.best_checkpoint = checkpoint

    def get_improvement_rate(self) -> float:
        """Calculate average improvement per epoch"""
        if len(self.performance_history) < 2:
            return 0.0

        first_acc = self.performance_history[0][1]
        last_acc = self.performance_history[-1][1]
        epochs = self.performance_history[-1][0] - self.performance_history[0][0]

        return (last_acc - first_acc) / max(epochs, 1)

    def has_plateau(self, window: int = 5) -> bool:
        """Detect if performance has plateaued"""
        if len(self.performance_history) < window:
            return False

        recent = self.performance_history[-window:]
        accuracies = [acc for _, acc in recent]

        # Plateau if variance is very small
        mean_acc = sum(accuracies) / len(accuracies)
        variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)

        return variance < 0.0001


class AdaptiveHyperparameterTuner:
    """Adaptively tune hyperparameters based on performance"""

    def __init__(self):
        self.tuning_history: List[Dict] = []
        self.current_params: Dict[str, float] = {
            "learning_rate": 0.01,
            "momentum": 0.9,
            "weight_decay": 0.0001,
            "dropout_rate": 0.5,
        }

    def get_suggestions(self, tracker: ModelEvolutionTracker) -> List[HyperparameterSuggestion]:
        """Generate hyperparameter suggestions based on training progress"""
        suggestions = []

        if tracker.has_plateau():
            # If plateaued, reduce learning rate
            suggestions.append(HyperparameterSuggestion(
                param_name="learning_rate",
                current_value=self.current_params["learning_rate"],
                suggested_value=self.current_params["learning_rate"] * 0.5,
                expected_improvement=5.0,  # % improvement
                confidence=0.7
            ))

        improvement_rate = tracker.get_improvement_rate()
        if improvement_rate > 0.01:  # Fast improvement
            # Can afford higher learning rate
            suggestions.append(HyperparameterSuggestion(
                param_name="learning_rate",
                current_value=self.current_params["learning_rate"],
                suggested_value=self.current_params["learning_rate"] * 1.2,
                expected_improvement=2.0,
                confidence=0.6
            ))

        # Suggest dropout adjustment based on overfitting
        if tracker.best_checkpoint:
            loss_ratio = tracker.best_checkpoint.loss / max(tracker.best_checkpoint.accuracy, 0.1)
            if loss_ratio > 2.0:  # High loss relative to accuracy = overfitting
                suggestions.append(HyperparameterSuggestion(
                    param_name="dropout_rate",
                    current_value=self.current_params["dropout_rate"],
                    suggested_value=min(self.current_params["dropout_rate"] * 1.1, 0.7),
                    expected_improvement=3.0,
                    confidence=0.65
                ))

        return suggestions

    def apply_suggestion(self, suggestion: HyperparameterSuggestion):
        """Apply a hyperparameter suggestion"""
        self.current_params[suggestion.param_name] = suggestion.suggested_value
        self.tuning_history.append({
            "param": suggestion.param_name,
            "from": suggestion.current_value,
            "to": suggestion.suggested_value,
            "expected_improvement": suggestion.expected_improvement,
        })

    def get_statistics(self) -> Dict[str, float]:
        """Get tuning statistics"""
        return {
            "adjustments_made": len(self.tuning_history),
            "learning_rate": self.current_params["learning_rate"],
            "dropout_rate": self.current_params["dropout_rate"],
        }


class ModelSelector:
    """Select best model from multiple candidates"""

    def __init__(self):
        self.candidates: List[Tuple[str, ModelCheckpoint]] = []

    def add_model(self, model_id: str, checkpoint: ModelCheckpoint):
        """Add a model candidate"""
        self.candidates.append((model_id, checkpoint))

    def select_best(self, metric: str = "accuracy") -> Optional[Tuple[str, ModelCheckpoint]]:
        """Select best model by metric"""
        if not self.candidates:
            return None

        if metric == "accuracy":
            best = max(self.candidates, key=lambda x: x[1].accuracy)
        elif metric == "loss":
            best = min(self.candidates, key=lambda x: x[1].loss)
        else:
            return None

        return best

    def get_ensemble_weights(self) -> Dict[str, float]:
        """Generate ensemble weights based on performance"""
        if not self.candidates:
            return {}

        # Calculate weights proportional to accuracy
        total_acc = sum(cp.accuracy for _, cp in self.candidates)
        weights = {
            model_id: cp.accuracy / total_acc
            for model_id, cp in self.candidates
        }

        return weights

    def get_statistics(self) -> Dict[str, float]:
        """Get model selection statistics"""
        if not self.candidates:
            return {"num_models": 0.0}

        accuracies = [cp.accuracy for _, cp in self.candidates]
        return {
            "num_models": len(self.candidates),
            "best_accuracy": max(accuracies),
            "avg_accuracy": sum(accuracies) / len(accuracies),
            "accuracy_spread": max(accuracies) - min(accuracies),
        }


class GridSearchOptimizer:
    """Grid search over hyperparameter space"""

    def __init__(self):
        self.param_grid: Dict[str, List[float]] = {}
        self.search_results: List[Tuple[Dict[str, float], float]] = []

    def set_param_grid(self, grid: Dict[str, List[float]]):
        """Define hyperparameter search space"""
        self.param_grid = grid

    def get_total_combinations(self) -> int:
        """Calculate total grid search combinations"""
        if not self.param_grid:
            return 0

        total = 1
        for values in self.param_grid.values():
            total *= len(values)

        return total

    def record_result(self, params: Dict[str, float], accuracy: float):
        """Record search result"""
        self.search_results.append((params.copy(), accuracy))

    def get_best_params(self) -> Optional[Dict[str, float]]:
        """Get best parameters found"""
        if not self.search_results:
            return None

        best_params, _ = max(self.search_results, key=lambda x: x[1])
        return best_params

    def estimate_search_cost(self, time_per_eval: float) -> float:
        """Estimate total search time in hours"""
        combinations = self.get_total_combinations()
        total_seconds = combinations * time_per_eval
        return total_seconds / 3600.0

    def get_statistics(self) -> Dict:
        """Get search statistics"""
        if not self.search_results:
            return {"combinations_tried": 0.0}

        accuracies = [acc for _, acc in self.search_results]
        return {
            "combinations_tried": len(self.search_results),
            "total_combinations": self.get_total_combinations(),
            "best_accuracy": max(accuracies),
            "avg_accuracy": sum(accuracies) / len(accuracies),
            "search_coverage": (len(self.search_results) / self.get_total_combinations()) * 100.0,
        }
