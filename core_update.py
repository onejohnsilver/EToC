#!/usr/bin/env python3
"""
core_update.py

State-update layer for the Evolutionary Survival Theory of Consciousness.

Modifications for Operator Testing:
    - Integrated MemoryManager from core_memory.py.
    - Added Allostatic Anticipation: Past trauma from the Salience Bank 
      now dynamically distorts prediction error, precision, and affect.
    - Memory routing strictly respects non-breaking TheoryState dictionaries.
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
# OPERATOR ADDITION: Bring in the new dual-track memory architecture
from core_memory import MemoryManager


class TheoryUpdater:
    """
    Applies the theory math to persistent state.
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
        
        # Initialize the dynamic memory bank
        self.memory_manager = MemoryManager(max_traces=self.config.memory_limit)
        if self.state.memory:
            self.memory_manager.sync_from_state(self.state)

    # --------------------------------------------------------
    # Update logic
    # --------------------------------------------------------

    def step(self, inputs: TheoryInputs) -> TheoryState:
        """Advance the state by one step using the full equation chain."""
        x = inputs
        w = self.weights
        s = self.state

        # --- OPERATOR INTERVENTION: Allostatic Anticipation ---
        # Calculate how much trauma the agent is carrying from the Salience Bank.
        # This prevents the agent from reacting naively to a dangerous environment.
        salient_traces = self.memory_manager.salient_traces()
        allostatic_load = 0.0
        if salient_traces:
            # Average the threat and error of permanent traumatic memories
            allostatic_load = sum(t.survival_loss + t.prediction_error for t in salient_traces) / (2.0 * len(salient_traces))

        # 1) Survival / thermodynamic layer
        loss = survival_loss(x, w)
        boundary = boundary_integrity_from_survival_loss(loss)

        # 2) Prediction layer (Subject to Anticipatory Anxiety)
        base_pe = prediction_error(x)
        base_precision = predictive_precision(x, boundary)
        
        # Trauma spikes baseline error and shatters precision certainty
        pe = min(1.0, base_pe + (allostatic_load * 0.40))
        precision = max(0.0, base_precision - (allostatic_load * 0.35))

        # 3) Affect / valuation layer (Subject to Orthogonal Pain)
        base_valence, base_arousal = affect(x, loss, pe)
        
        # High allostatic load makes valence more negative and keeps arousal elevated
        valence = max(-1.0, base_valence - (allostatic_load * 0.30))
        arousal = min(1.0, base_arousal + (allostatic_load * 0.50))

        # 4) Self-model and social model
        self_depth = self_model_depth(w, boundary, pe, x)
        social_depth = social_model_depth(w, x)

        # 5) Recursive integration
        recursion = recursive_integration(w, self_depth, social_depth, x)

        # 6) Global integration and subjective experience
        global_int = global_integration(boundary, self_depth, social_depth, recursion)
        subjective = subjective_experience(
            w,
            valence,
            arousal,
            pe,
            self_depth,
            social_depth,
            recursion,
            x.peer_prediction_accuracy,
        )

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
            # We clear this temporarily; MemoryManager will inject the formatted list
            memory=[], 
        )

        # 9) Route memory through the manager to evaluate Salience, then inject back
        self.memory_manager.store(updated)
        self.state = self.memory_manager.inject_into_state(updated)
        
        return self.state

    def reset(self, state: Optional[TheoryState] = None) -> TheoryState:
        """Reset the evolving state."""
        self.state = state or TheoryState()
        self.memory_manager = MemoryManager(max_traces=self.config.memory_limit)
        if self.state.memory:
            self.memory_manager.sync_from_state(self.state)
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
        """
        disabled_layers = disabled_layers or []
        x = inputs
        w = self.weights
        s = self.state
        
        # Apply the same Allostatic Anticipation to ablation tests
        salient_traces = self.memory_manager.salient_traces()
        allostatic_load = 0.0
        if salient_traces:
            allostatic_load = sum(t.survival_loss + t.prediction_error for t in salient_traces) / (2.0 * len(salient_traces))

        loss = survival_loss(x, w) if "survival" not in disabled_layers else 0.0
        boundary = boundary_integrity_from_survival_loss(loss) if "boundary" not in disabled_layers else 0.0
        
        base_pe = prediction_error(x) if "prediction" not in disabled_layers else 0.0
        base_precision = predictive_precision(x, boundary) if "prediction" not in disabled_layers else 0.0
        
        pe = min(1.0, base_pe + (allostatic_load * 0.40)) if "prediction" not in disabled_layers else 0.0
        precision = max(0.0, base_precision - (allostatic_load * 0.35)) if "prediction" not in disabled_layers else 0.0
        
        if "affect" not in disabled_layers:
            base_valence, base_arousal = affect(x, loss, pe)
            valence = max(-1.0, base_valence - (allostatic_load * 0.30))
            arousal = min(1.0, base_arousal + (allostatic_load * 0.50))
        else:
            valence, arousal = 0.0, 0.0
            
        self_depth = self_model_depth(w, boundary, pe, x) if "self_model" not in disabled_layers else 0.0
        social_depth = social_model_depth(w, x) if "social_model" not in disabled_layers else 0.0
        recursion = recursive_integration(w, self_depth, social_depth, x) if "recursion" not in disabled_layers else 0.0
        global_int = (
            global_integration(boundary, self_depth, social_depth, recursion)
            if "subjective_experience" not in disabled_layers
            else 0.0
        )
        subjective = (
            subjective_experience(
                w,
                valence,
                arousal,
                pe,
                self_depth,
                social_depth,
                recursion,
                x.peer_prediction_accuracy,
            )
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
            memory=[],
        )

        self.memory_manager.store(updated)
        self.state = self.memory_manager.inject_into_state(updated)
        
        return self.state


# ------------------------------------------------------------
# Internal smoothing helper
# ------------------------------------------------------------


def _smooth(previous: float, new_value: float, alpha: float = 0.25) -> float:
    """Exponential smoothing keeps the evolving state stable over time."""
    return (1.0 - alpha) * previous + alpha * new_value