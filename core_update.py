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
from typing import Dict, List, Optional

from core_types import TheoryConfig, TheoryInputs, TheoryState, TheoryWeights, LayerName
from core_math import (
    TheoryMathOutput,
    affect,
    boundary_integrity_from_survival_loss,
    clamp,
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
        self.regret_history: List[float] = []
        self.last_regret: float = 0.0
        
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
        # Compose somatic reserve from available inputs and weight by importance
        somatic_weights = (
            w.w_metabolic_deficit + w.w_hydration_deficit + w.w_oxygenation_deficit + w.w_neural_energy_deficit
        )
        if somatic_weights > 0.0:
            somatic_reserve = (
                w.w_metabolic_deficit * x.metabolic_reserve
                + w.w_hydration_deficit * x.hydration
                + w.w_oxygenation_deficit * x.oxygenation
                + w.w_neural_energy_deficit * x.neural_energy
            ) / somatic_weights
        else:
            somatic_reserve = 1.0

        boundary = boundary_integrity_from_survival_loss(loss, somatic_reserve)

        # 2) Prediction layer (Subject to Anticipatory Anxiety)
        base_pe = prediction_error(x)
        base_precision = predictive_precision(x, boundary)
        
        # Gentle allostatic modulation: soft anticipatory bias without permanent ceiling
        trauma_weight = 0.7 * allostatic_load
        pe = min(1.0, base_pe + (trauma_weight * 0.05))
        precision = max(0.0, base_precision - (trauma_weight * 0.04))

        # 3) Affect / valuation layer (Subject to Orthogonal Pain)
        base_valence, base_arousal = affect(x, loss, pe)
        
        # Mild allostatic affect modulation: memories inform caution without crushing resilience
        # Goal context can soften threat if aligned, or increase pressure if urgency is high.
        goal_bias = 0.10 * x.goal_alignment - 0.05 * x.goal_urgency
        valence = max(-1.0, base_valence - (trauma_weight * 0.03) + goal_bias)
        arousal = min(1.0, base_arousal + (trauma_weight * 0.06) + (0.05 * x.goal_urgency))

        # 4) Self-model and social model
        self_depth = clamp(
            self_model_depth(w, boundary, pe, x)
            + 0.10 * x.goal_alignment
            + 0.10 * x.meta_accuracy,
            0.0,
            1.0,
        )
        social_depth = social_model_depth(w, x)
        epistemic_gate = clamp(1.0 - 0.6 * pe, 0.0, 1.0)
        social_depth = social_depth * epistemic_gate

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
            boundary,
        )

        # 7) Consciousness index with diminishing amplification from recursion
        consciousness_base = consciousness_index(w, subjective, global_int, boundary)
        # Diminishing returns: as base consciousness approaches 1.0, less room to amplify
        amplification_capacity = max(0.0, 1.0 - consciousness_base)
        recursion_bonus = 0.10 * recursion * x.meta_accuracy * amplification_capacity
        consciousness = clamp(consciousness_base + recursion_bonus, 0.0, 1.0)

        # 8) Persist the new state with gentle smoothing
        updated = TheoryState(
            viability=_smooth(s.viability, 1.0 - 0.50 * loss),
            boundary_integrity=_smooth(s.boundary_integrity, boundary),
            thermodynamic_load=_smooth_adaptive(s.thermodynamic_load, loss),
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
        self.regret_history = []
        self.last_regret = 0.0
        if self.state.memory:
            self.memory_manager.sync_from_state(self.state)
        return self.state

    def get_state(self) -> TheoryState:
        return self.state

    def record_regret(self, regret: float) -> None:
        self.last_regret = clamp(regret, 0.0, 1.0)
        self.regret_history.append(self.last_regret)

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
            "last_regret": self.last_regret,
            "average_regret": sum(self.regret_history) / len(self.regret_history) if self.regret_history else 0.0,
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
        # ablation: still compute somatic_reserve for boundary unless boundary disabled
        somatic_weights = (
            w.w_metabolic_deficit + w.w_hydration_deficit + w.w_oxygenation_deficit + w.w_neural_energy_deficit
        )
        if somatic_weights > 0.0:
            somatic_reserve = (
                w.w_metabolic_deficit * x.metabolic_reserve
                + w.w_hydration_deficit * x.hydration
                + w.w_oxygenation_deficit * x.oxygenation
                + w.w_neural_energy_deficit * x.neural_energy
            ) / somatic_weights
        else:
            somatic_reserve = 1.0

        boundary = (
            boundary_integrity_from_survival_loss(loss, somatic_reserve)
            if "boundary" not in disabled_layers
            else 0.0
        )
        
        base_pe = prediction_error(x) if "prediction" not in disabled_layers else 0.0
        base_precision = predictive_precision(x, boundary) if "prediction" not in disabled_layers else 0.0
        
        pe = min(1.0, base_pe + (allostatic_load * 0.12)) if "prediction" not in disabled_layers else 0.0
        precision = max(0.0, base_precision - (allostatic_load * 0.10)) if "prediction" not in disabled_layers else 0.0
        
        if "affect" not in disabled_layers:
            base_valence, base_arousal = affect(x, loss, pe)
            valence = max(-1.0, base_valence - (allostatic_load * 0.08))
            arousal = min(1.0, base_arousal + (allostatic_load * 0.15))
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
            thermodynamic_load=_smooth_adaptive(s.thermodynamic_load, loss),
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


def _smooth_adaptive(previous: float, new_value: float) -> float:
    """Adaptive exponential smoothing: react faster to large changes.

    Alpha ranges from 0.10 (small changes) up to 0.50 (sudden changes).
    """
    delta = abs(new_value - previous)
    alpha = 0.10 + 0.40 * min(1.0, delta / 0.5)
    return (1.0 - alpha) * previous + alpha * new_value