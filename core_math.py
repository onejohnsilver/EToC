#!/usr/bin/env python3
"""
core_math.py

Precise equation layer for the Evolutionary Survival Theory of Consciousness.

This file contains the theory math only.
It does not define the simulation loop, environment, or agent behavior.
It takes TheoryInputs and TheoryWeights from core_types.py and returns
layer values that later files can assemble into state updates.

Equation order:
    1. Survival loss
    2. Boundary integrity
    3. Prediction error
    4. Predictive precision
    5. Affect (valence + arousal)
    6. Self-model depth
    7. Social model depth
    8. Recursive integration
    9. Global integration
    10. Subjective experience proxy
    11. Consciousness index
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

    L_survival =
        w_homeostasis * homeostatic_deviation
      + w_environment * environmental_stress
      + w_prediction_error * |prediction_target - observed_state|
      + w_action_cost * action_cost
      + w_social_threat * social_threat
      - w_social_support * social_support
      - w_language * language_support
      - w_memory * memory_depth
    """
    x = x
    return (
        w.w_homeostasis * x.homeostatic_deviation
        + w.w_environment * x.environmental_stress
        + w.w_prediction_error * abs(x.prediction_target - x.observed_state)
        + w.w_action_cost * x.action_cost
        + w.w_social_threat * x.social_threat
        - w.w_social_support * x.social_support
        - w.w_language * x.language_support
        - w.w_memory * x.memory_depth
    )


def boundary_integrity_from_survival_loss(loss: float) -> float:
    """
    Boundary integrity is an inverse transform of survival loss.

    B = sigmoid(2.5 * (0.5 - loss))

    High loss -> weak boundary integrity.
    Low loss -> strong boundary integrity.
    """
    return clamp(sigmoid(2.5 * (0.5 - loss)), 0.0, 1.0)


def prediction_error(x: TheoryInputs) -> float:
    """Basic prediction error: absolute mismatch between expected and observed."""
    return abs(x.prediction_target - x.observed_state)


def predictive_precision(x: TheoryInputs, boundary_integrity_value: float) -> float:
    """
    Predictive precision is increased by stable boundary integrity and memory,
    and decreased by external uncertainty.

    P = 0.50*boundary_integrity + 0.25*memory_depth + 0.25*(1 - external_uncertainty)
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

    Valence:
        V = 1 - clamp(0.55*loss + 0.45*social_threat, 0, 1.5)

    Arousal:
        A = clamp(0.45*environmental_stress + 0.35*prediction_error + 0.20*social_threat, 0, 1)
    """
    valence = 1.0 - clamp(0.55 * loss + 0.45 * x.social_threat, 0.0, 1.5)
    arousal = clamp(0.45 * x.environmental_stress + 0.35 * pe + 0.20 * x.social_threat, 0.0, 1.0)
    return valence, arousal


def self_model_depth(
    w: TheoryWeights,
    boundary_integrity_value: float,
    pe: float,
    x: TheoryInputs,
) -> float:
    """
    Self-model depth is a boundary + prediction + memory function.

    S = w_self_from_boundary * boundary_integrity
      + w_self_from_prediction * (1 - prediction_error)
      + w_self_from_memory * memory_depth
    """
    value = (
        w.w_self_from_boundary * boundary_integrity_value
        + w.w_self_from_prediction * (1.0 - pe)
        + w.w_self_from_memory * x.memory_depth
    )
    return clamp(value, 0.0, 1.0)


def social_model_depth(w: TheoryWeights, x: TheoryInputs) -> float:
    """
    Social model depth tracks both threat and support because both require modeling others.

    M_social =
        w_social_from_threat * social_threat
      + w_social_from_support * social_support
      + w_social_from_language * language_support
    """
    value = (
        w.w_social_from_threat * x.social_threat
        + w.w_social_from_support * x.social_support
        + w.w_social_from_language * x.language_support
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

    R = w_recursion_self * self_model
      + w_recursion_social * social_model
      + w_recursion_language * (0.5*language_support + 0.5*memory_depth)
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

    G = 0.25*boundary + 0.25*self + 0.20*social + 0.30*recursion
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
) -> float:
    """
    Proxy for felt first-person integration.

    First convert affect into a bad-to-good load term:
        affect_component = 0.5*(1 - valence) + 0.5*arousal

    Then integrate with prediction, self, social, and recursion.
    """
    affect_component = 0.50 * (1.0 - affect_valence_value) + 0.50 * affect_arousal_value
    value = (
        w.w_subjective_affect * affect_component
        + w.w_subjective_prediction * pe
        + w.w_subjective_self * self_model_value
        + w.w_subjective_social * social_model_value
        + w.w_subjective_recursion * recursive_value
    )
    return clamp(value, 0.0, 1.0)


def consciousness_index(
    w: TheoryWeights,
    subjective_value: float,
    global_value: float,
    boundary_integrity_value: float,
) -> float:
    """
    Final consciousness score.

    C = w_subjective * subjective_experience
      + w_global * global_integration
      + w_boundary * boundary_integrity
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
    boundary = boundary_integrity_from_survival_loss(loss)
    pe = prediction_error(x)
    precision = predictive_precision(x, boundary)
    valence, arousal = affect(x, loss, pe)
    self_depth = self_model_depth(w, boundary, pe, x)
    social_depth = social_model_depth(w, x)
    recursion = recursive_integration(w, self_depth, social_depth, x)
    global_int = global_integration(boundary, self_depth, social_depth, recursion)
    subjective = subjective_experience(w, valence, arousal, pe, self_depth, social_depth, recursion)
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
