#!/usr/bin/env python3
"""
core_update.py

State-update layer for the Evolutionary Survival Theory of Consciousness.

This file applies the equations from core_math.py step by step to evolve state.
It does not define the equations themselves.
It only defines update order, persistence, and memory handling.

Update order:
    1. Read inputs
    2. Compute equation outputs in theory order
    3. Smooth / persist state over time
    4. Append memory
    5. Return updated state
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Optional

from core_types import TheoryConfig, TheoryInputs, TheoryState, TheoryWeights, LayerName
from core_math import (
    TheoryMathOutput,
    affect,
    boundary_integrity_from_survival_loss,
    consciousness_index,
    compute_all,
    global_integration,
    predictive_precision,
    prediction_error,
    recursive_integration,
    self_model_depth,
    social_model_depth,
    subjective_experience,
    survival_loss,
)


class TheoryUpdater:
    """
    Applies the theory math to persistent state.

    The core principle is:
        inputs -> equations -> evolving state

    The updater is intentionally thin. It orchestrates the order without
    redefining the math.
    """

    def __init__(
        self,
        weights: Optional[TheoryWeights] = None,
        config: Optional[TheoryConfig] = None,
        initial_state: Optional[TheoryState] = None,
    ):
        self.weights = weights or TheoryWeights()
        self.config = config or TheoryConfig()
        self.state = initial_state or TheoryState()

    # --------------------------------------------------------
    # Update logic
    # --------------------------------------------------------

    def step(self, inputs: TheoryInputs) -> TheoryState:
        """Advance the state by one step using the full equation chain."""
        x = inputs
        w = self.weights
        s = self.state

        # 1) Survival / thermodynamic layer
        loss = survival_loss(x, w)
        boundary = boundary_integrity_from_survival_loss(loss)

        # 2) Prediction layer
        pe = prediction_error(x)
        precision = predictive_precision(x, boundary)

        # 3) Affect / valuation layer
        valence, arousal = affect(x, loss, pe)

        # 4) Self-model and social model
        self_depth = self_model_depth(w, boundary, pe, x)
        social_depth = social_model_depth(w, x)

        # 5) Recursive integration
        recursion = recursive_integration(w, self_depth, social_depth, x)

        # 6) Global integration and subjective experience
        global_int = global_integration(boundary, self_depth, social_depth, recursion)
        subjective = subjective_experience(w, valence, arousal, pe, self_depth, social_depth, recursion)

        # 7) Consciousness index
        consciousness = consciousness_index(w, subjective, global_int, boundary)

        # 8) Persist the new state with gentle smoothing
        updated = TheoryState(
            viability=_smooth(s.viability, 1.0 - 0.50 * loss),
            boundary_integrity=_smooth(s.boundary_integrity, boundary),
            thermodynamic_load=_smooth(s.thermodynamic_load, loss),
            survival_loss=loss,
            prediction_error=_smooth(s.prediction_error, pe),
            predictive_precision=_smooth(s.predictive_precision, precision),
            affect_valence=_smooth(s.affect_valence, valence),
            affect_arousal=_smooth(s.affect_arousal, arousal),
            self_model_depth=_smooth(s.self_model_depth, self_depth),
            social_model_depth=_smooth(s.social_model_depth, social_depth),
            recursive_integration=_smooth(s.recursive_integration, recursion),
            language_stability=_smooth(s.language_stability, x.language_support),
            subjective_experience=_smooth(s.subjective_experience, subjective),
            consciousness_index=_smooth(s.consciousness_index, consciousness),
            global_integration=_smooth(s.global_integration, global_int),
            step_index=s.step_index + 1,
            memory=[*s.memory],
        )

        # 9) Append a compact memory trace
        updated.memory.append(
            {
                "step_index": float(updated.step_index),
                "survival_loss": loss,
                "boundary_integrity": boundary,
                "prediction_error": pe,
                "predictive_precision": precision,
                "affect_valence": valence,
                "affect_arousal": arousal,
                "self_model_depth": self_depth,
                "social_model_depth": social_depth,
                "recursive_integration": recursion,
                "global_integration": global_int,
                "subjective_experience": subjective,
                "consciousness_index": consciousness,
            }
        )
        updated.memory = updated.memory[-self.config.memory_limit :]

        self.state = updated
        return self.state

    def reset(self, state: Optional[TheoryState] = None) -> TheoryState:
        """Reset the evolving state."""
        self.state = state or TheoryState()
        return self.state

    def get_state(self) -> TheoryState:
        return self.state

    def get_metrics(self) -> Dict[str, float]:
        """Simple metrics view for later tests and visualizations."""
        s = self.state
        return {
            "viability": s.viability,
            "boundary_integrity": s.boundary_integrity,
            "thermodynamic_load": s.thermodynamic_load,
            "survival_loss": s.survival_loss,
            "prediction_error": s.prediction_error,
            "predictive_precision": s.predictive_precision,
            "affect_valence": s.affect_valence,
            "affect_arousal": s.affect_arousal,
            "self_model_depth": s.self_model_depth,
            "social_model_depth": s.social_model_depth,
            "recursive_integration": s.recursive_integration,
            "language_stability": s.language_stability,
            "subjective_experience": s.subjective_experience,
            "consciousness_index": s.consciousness_index,
            "global_integration": s.global_integration,
            "step_index": float(s.step_index),
        }

    def ablation_step(self, inputs: TheoryInputs, disabled_layers: Optional[list[LayerName]] = None) -> TheoryState:
        """
        One-step update with selected layers set aside.

        This is intentionally simple: later files can use it to test the role
        of specific layers without changing the full engine.
        """
        disabled_layers = disabled_layers or []
        x = inputs
        w = self.weights
        s = self.state

        loss = survival_loss(x, w) if "survival" not in disabled_layers else 0.0
        boundary = boundary_integrity_from_survival_loss(loss) if "boundary" not in disabled_layers else 0.0
        pe = prediction_error(x) if "prediction" not in disabled_layers else 0.0
        precision = predictive_precision(x, boundary) if "prediction" not in disabled_layers else 0.0
        valence, arousal = affect(x, loss, pe) if "affect" not in disabled_layers else (0.0, 0.0)
        self_depth = self_model_depth(w, boundary, pe, x) if "self_model" not in disabled_layers else 0.0
        social_depth = social_model_depth(w, x) if "social_model" not in disabled_layers else 0.0
        recursion = recursive_integration(w, self_depth, social_depth, x) if "recursion" not in disabled_layers else 0.0
        global_int = (
            global_integration(boundary, self_depth, social_depth, recursion)
            if "subjective_experience" not in disabled_layers
            else 0.0
        )
        subjective = (
            subjective_experience(w, valence, arousal, pe, self_depth, social_depth, recursion)
            if "subjective_experience" not in disabled_layers
            else 0.0
        )
        consciousness = (
            consciousness_index(w, subjective, global_int, boundary)
            if "consciousness" not in disabled_layers
            else 0.0
        )

        updated = TheoryState(
            viability=_smooth(s.viability, 1.0 - 0.50 * loss),
            boundary_integrity=_smooth(s.boundary_integrity, boundary),
            thermodynamic_load=_smooth(s.thermodynamic_load, loss),
            survival_loss=loss,
            prediction_error=_smooth(s.prediction_error, pe),
            predictive_precision=_smooth(s.predictive_precision, precision),
            affect_valence=_smooth(s.affect_valence, valence),
            affect_arousal=_smooth(s.affect_arousal, arousal),
            self_model_depth=_smooth(s.self_model_depth, self_depth),
            social_model_depth=_smooth(s.social_model_depth, social_depth),
            recursive_integration=_smooth(s.recursive_integration, recursion),
            language_stability=_smooth(s.language_stability, x.language_support),
            subjective_experience=_smooth(s.subjective_experience, subjective),
            consciousness_index=_smooth(s.consciousness_index, consciousness),
            global_integration=_smooth(s.global_integration, global_int),
            step_index=s.step_index + 1,
            memory=[*s.memory],
        )
        updated.memory.append(
            {
                "step_index": float(updated.step_index),
                "survival_loss": loss,
                "boundary_integrity": boundary,
                "prediction_error": pe,
                "predictive_precision": precision,
                "affect_valence": valence,
                "affect_arousal": arousal,
                "self_model_depth": self_depth,
                "social_model_depth": social_depth,
                "recursive_integration": recursion,
                "global_integration": global_int,
                "subjective_experience": subjective,
                "consciousness_index": consciousness,
            }
        )
        updated.memory = updated.memory[-self.config.memory_limit :]

        self.state = updated
        return self.state


# ------------------------------------------------------------
# Internal smoothing helper
# ------------------------------------------------------------


def _smooth(previous: float, new_value: float, alpha: float = 0.25) -> float:
    """Exponential smoothing keeps the evolving state stable over time."""
    return (1.0 - alpha) * previous + alpha * new_value
