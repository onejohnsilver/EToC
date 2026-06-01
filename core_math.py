#!/usr/bin/env python3
"""
core_math.py

Precise equation layer for the Evolutionary Survival Theory of Consciousness.

Operator Modifications:
    - Implemented Orthogonal Costing in the Affect layer. 
      Extreme physical or social pain now acts as a non-reducible priority gate,
      overriding standard linear valuation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, Tuple

from core_types import TheoryInputs, TheoryWeights


# ============================================================
# Helpers
# ============================================================


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# ============================================================
# Equation outputs
# ============================================================


@dataclass(frozen=True)
class TheoryMathOutput:
    """One-step equation outputs, kept separate from persistent state."""

    survival_loss: float
    boundary_integrity: float
    prediction_error: float
    predictive_precision: float
    affect_valence: float
    affect_arousal: float
    self_model_depth: float
    social_model_depth: float
    recursive_integration: float
    global_integration: float
    subjective_experience: float
    consciousness_index: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "survival_loss": self.survival_loss,
            "boundary_integrity": self.boundary_integrity,
            "prediction_error": self.prediction_error,
            "predictive_precision": self.predictive_precision,
            "affect_valence": self.affect_valence,
            "affect_arousal": self.affect_arousal,
            "self_model_depth": self.self_model_depth,
            "social_model_depth": self.social_model_depth,
            "recursive_integration": self.recursive_integration,
            "global_integration": self.global_integration,
            "subjective_experience": self.subjective_experience,
            "consciousness_index": self.consciousness_index,
        }


# ============================================================
# Core equations
# ============================================================


def survival_loss(x: TheoryInputs, w: TheoryWeights) -> float:
    """
    Thermodynamic / survival constraint.
    """
    x = x
    somatic_load = (
        w.w_metabolic_deficit * (1.0 - x.metabolic_reserve)
        + w.w_hydration_deficit * (1.0 - x.hydration)
        + w.w_oxygenation_deficit * (1.0 - x.oxygenation)
        + w.w_immune_load * x.immune_load
        + w.w_neural_energy_deficit * (1.0 - x.neural_energy)
    )
    return (
        w.w_homeostasis * x.homeostatic_deviation
        + w.w_environment * x.environmental_stress
        + w.w_prediction_error * abs(x.prediction_target - x.observed_state)
        + w.w_action_cost * x.action_cost
        + somatic_load
        + w.w_social_threat * x.social_threat
        - w.w_social_support * x.social_support
        - w.w_language * x.language_support
        - w.w_memory * x.memory_depth
    )


def boundary_integrity_from_survival_loss(loss: float, somatic_reserve: float = 1.0) -> float:
    """
    Compute boundary integrity from survival loss and embodied somatic reserve.

    The base boundary depends on survival loss; metabolic/somatic reserve gates
    the result so physically depleted agents have weaker boundaries.
    """
    base_boundary = clamp(sigmoid(2.5 * (0.5 - loss)), 0.0, 1.0)

    # Metabolic/somatic gate: at reserve=0 -> gate=0.4; at reserve=1 -> gate=1.0
    metabolic_gate = clamp(0.4 + 0.6 * somatic_reserve, 0.0, 1.0)

    return base_boundary * metabolic_gate


def prediction_error(x: TheoryInputs) -> float:
    """Basic prediction error: absolute mismatch between expected and observed."""
    return abs(x.prediction_target - x.observed_state)


def predictive_precision(x: TheoryInputs, boundary_integrity_value: float) -> float:
    """
    Predictive precision is increased by stable boundary integrity and memory,
    and decreased by external uncertainty.
    """
    precision = (
        0.50 * boundary_integrity_value
        + 0.25 * x.memory_depth
        + 0.25 * (1.0 - x.external_uncertainty)
    )
    return clamp(precision, 0.0, 1.0)


def affect(x: TheoryInputs, loss: float, pe: float) -> Tuple[float, float]:
    """
    Affect is split into valence and arousal.

    OPERATOR MODIFICATION: Orthogonal Priority Gating
    Pain (physical or social) acts as an independently effective, non-reducible cost signal.
    If either threat exceeds a threshold, it forces the valence deeply negative, 
    preventing the agent from "averaging out" severe trauma.
    """
    # 1. Calculate standard linear valence
    base_valence = 1.0 - clamp(0.55 * loss + 0.45 * x.social_threat, 0.0, 1.5)
    
    # 2. Apply Orthogonal Cost Override
    # If loss (physical pain) or social_threat (social pain) is critical, it overrides the average.
    orthogonal_cost = max(loss, x.social_threat)
    if orthogonal_cost > 0.60:
        # Exponentially pull valence downward as orthogonal cost approaches 1.0
        valence = clamp(base_valence - (orthogonal_cost ** 2), -1.0, 1.0)
    else:
        valence = clamp(base_valence, -1.0, 1.0)

    # Arousal spikes exponentially with prediction error and environmental stress
    arousal = clamp(0.45 * x.environmental_stress + 0.35 * pe + 0.20 * x.social_threat, 0.0, 1.0)
    
    return valence, arousal


def self_model_depth(
    w: TheoryWeights,
    boundary_integrity_value: float,
    pe: float,
    x: TheoryInputs,
) -> float:
    """
    Self-model depth is a boundary + prediction + memory + consistency function.
    """
    value = (
        w.w_self_from_boundary * boundary_integrity_value
        + w.w_self_from_prediction * (1.0 - pe)
        + w.w_self_from_memory * x.memory_depth
        + w.w_self_from_consistency * x.self_consistency
    )
    return clamp(value, 0.0, 1.0)


def social_model_depth(w: TheoryWeights, x: TheoryInputs) -> float:
    """
    Social model depth tracks both threat and support because both require modeling others.
    """
    value = (
        w.w_social_from_threat * x.social_threat
        + w.w_social_from_support * x.social_support
        + w.w_social_from_language * x.language_support
        + w.w_social_from_peer_prediction * x.peer_prediction_accuracy
    )
    return clamp(value, 0.0, 1.0)


def recursive_integration(
    w: TheoryWeights,
    self_model_value: float,
    social_model_value: float,
    x: TheoryInputs,
) -> float:
    """
    Recursion is self-modeling about self-modeling, strengthened by language and memory.
    """
    value = (
        w.w_recursion_self * self_model_value
        + w.w_recursion_social * social_model_value
        + w.w_recursion_language * (0.5 * x.language_support + 0.5 * x.memory_depth)
    )
    return clamp(value, 0.0, 1.0)


def global_integration(
    boundary_integrity_value: float,
    self_model_value: float,
    social_model_value: float,
    recursive_value: float,
) -> float:
    """
    A structural fusion score across the main layers.
    """
    value = (
        0.25 * boundary_integrity_value
        + 0.25 * self_model_value
        + 0.20 * social_model_value
        + 0.30 * recursive_value
    )
    return clamp(value, 0.0, 1.0)


def subjective_experience(
    w: TheoryWeights,
    affect_valence_value: float,
    affect_arousal_value: float,
    pe: float,
    self_model_value: float,
    social_model_value: float,
    recursive_value: float,
    peer_prediction_accuracy: float = 0.5,
    boundary_integrity_value: float = 1.0,
) -> float:
    """
    Proxy for felt first-person integration.
    """
    affect_component = 0.50 * (1.0 - affect_valence_value) + 0.50 * affect_arousal_value
    value = (
        w.w_subjective_affect * affect_component
        + w.w_subjective_prediction * pe
        + w.w_subjective_self * self_model_value
        + w.w_subjective_social * social_model_value
        + w.w_subjective_peer_prediction * peer_prediction_accuracy
        + w.w_subjective_recursion * recursive_value
    )

    # Survival gate: subjective experience is dampened when boundary integrity
    # is low or prediction error is high. Multiply (not add) to enforce gating.
    survival_gate = clamp(boundary_integrity_value * 0.70 + (1.0 - pe) * 0.30, 0.0, 1.0)
    value = value * survival_gate

    return clamp(value, 0.0, 1.0)


def consciousness_index(
    w: TheoryWeights,
    subjective_value: float,
    global_value: float,
    boundary_integrity_value: float,
) -> float:
    """
    Final consciousness score.
    """
    value = (
        w.w_consciousness_subjective * subjective_value
        + w.w_consciousness_global_integration * global_value
        + w.w_consciousness_boundary * boundary_integrity_value
    )
    return clamp(value, 0.0, 1.0)


# ============================================================
# Composite calculator
# ============================================================


def compute_all(x: TheoryInputs, w: TheoryWeights) -> TheoryMathOutput:
    """Convenience function that runs the full equation chain in the theory order."""
    loss = survival_loss(x, w)
    # Compose a somatic reserve score from the most relevant physiological signals.
    somatic_weights = (
        w.w_metabolic_deficit
        + w.w_hydration_deficit
        + w.w_oxygenation_deficit
        + w.w_neural_energy_deficit
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
    pe = prediction_error(x)
    precision = predictive_precision(x, boundary)
    valence, arousal = affect(x, loss, pe)
    self_depth = self_model_depth(w, boundary, pe, x)
    social_depth = social_model_depth(w, x)
    recursion = recursive_integration(w, self_depth, social_depth, x)
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
    consciousness = consciousness_index(w, subjective, global_int, boundary)

    return TheoryMathOutput(
        survival_loss=loss,
        boundary_integrity=boundary,
        prediction_error=pe,
        predictive_precision=precision,
        affect_valence=valence,
        affect_arousal=arousal,
        self_model_depth=self_depth,
        social_model_depth=social_depth,
        recursive_integration=recursion,
        global_integration=global_int,
        subjective_experience=subjective,
        consciousness_index=consciousness,
    )
