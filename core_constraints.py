#!/usr/bin/env python3
"""
core_constraints.py

Constraint / invariants layer for the Evolutionary Survival Theory of Consciousness.

This file does not define the theory equations.
It enforces valid ranges, normalization rules, and structural invariants so the
math engine remains stable before memory and ablation logic are added.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from core_types import TheoryInputs, TheoryState


# ============================================================
# Basic helpers
# ============================================================


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ============================================================
# Constraint report
# ============================================================


@dataclass(frozen=True)
class ConstraintIssue:
    """A single constraint violation or warning."""

    field_name: str
    message: str


@dataclass(frozen=True)
class ConstraintReport:
    """Validation result for inputs or state."""

    valid: bool
    issues: Tuple[ConstraintIssue, ...]


# ============================================================
# Input constraints
# ============================================================


def sanitize_inputs(x: TheoryInputs) -> TheoryInputs:
    """
    Clamp raw inputs to safe ranges.

    The theory assumes normalized values for stable math.
    """
    return TheoryInputs(
        homeostatic_deviation=clamp(x.homeostatic_deviation, 0.0, 1.0),
        environmental_stress=clamp(x.environmental_stress, 0.0, 1.0),
        prediction_target=clamp(x.prediction_target, 0.0, 1.0),
        observed_state=clamp(x.observed_state, 0.0, 1.0),
        social_threat=clamp(x.social_threat, 0.0, 1.0),
        social_support=clamp(x.social_support, 0.0, 1.0),
        language_support=clamp(x.language_support, 0.0, 1.0),
        action_cost=clamp(x.action_cost, 0.0, 1.0),
        memory_depth=clamp(x.memory_depth, 0.0, 1.0),
        self_consistency=clamp(x.self_consistency, 0.0, 1.0),
        external_uncertainty=clamp(x.external_uncertainty, 0.0, 1.0),
    )


def validate_inputs(x: TheoryInputs) -> ConstraintReport:
    """Check whether the inputs are already within valid theory bounds."""
    issues: List[ConstraintIssue] = []
    fields = {
        "homeostatic_deviation": x.homeostatic_deviation,
        "environmental_stress": x.environmental_stress,
        "prediction_target": x.prediction_target,
        "observed_state": x.observed_state,
        "social_threat": x.social_threat,
        "social_support": x.social_support,
        "language_support": x.language_support,
        "action_cost": x.action_cost,
        "memory_depth": x.memory_depth,
        "self_consistency": x.self_consistency,
        "external_uncertainty": x.external_uncertainty,
    }
    for name, value in fields.items():
        if not (0.0 <= value <= 1.0):
            issues.append(
                ConstraintIssue(
                    field_name=name,
                    message=f"{name}={value} is outside the allowed range [0, 1].",
                )
            )
    return ConstraintReport(valid=(len(issues) == 0), issues=tuple(issues))


# ============================================================
# State constraints
# ============================================================


def sanitize_state(s: TheoryState) -> TheoryState:
    """
    Clamp state variables to safe ranges and preserve structural consistency.

    This keeps the engine numerically stable over long runs.
    """
    s.viability = clamp(s.viability, 0.0, 1.0)
    s.boundary_integrity = clamp(s.boundary_integrity, 0.0, 1.0)
    s.thermodynamic_load = clamp(s.thermodynamic_load, 0.0, 2.0)
    s.survival_loss = clamp(s.survival_loss, -2.0, 2.0)

    s.prediction_error = clamp(s.prediction_error, 0.0, 1.0)
    s.predictive_precision = clamp(s.predictive_precision, 0.0, 1.0)
    s.affect_valence = clamp(s.affect_valence, 0.0, 1.0)
    s.affect_arousal = clamp(s.affect_arousal, 0.0, 1.0)

    s.self_model_depth = clamp(s.self_model_depth, 0.0, 1.0)
    s.social_model_depth = clamp(s.social_model_depth, 0.0, 1.0)
    s.recursive_integration = clamp(s.recursive_integration, 0.0, 1.0)
    s.language_stability = clamp(s.language_stability, 0.0, 1.0)

    s.subjective_experience = clamp(s.subjective_experience, 0.0, 1.0)
    s.consciousness_index = clamp(s.consciousness_index, 0.0, 1.0)
    s.global_integration = clamp(s.global_integration, 0.0, 1.0)

    s.step_index = max(0, int(s.step_index))
    return s


def validate_state(s: TheoryState) -> ConstraintReport:
    """Check whether the state respects the theory's invariants."""
    issues: List[ConstraintIssue] = []

    bounded_01 = {
        "viability": s.viability,
        "boundary_integrity": s.boundary_integrity,
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
    }
    for name, value in bounded_01.items():
        if not (0.0 <= value <= 1.0):
            issues.append(ConstraintIssue(name, f"{name}={value} is outside [0, 1]."))

    if s.thermodynamic_load < 0.0:
        issues.append(ConstraintIssue("thermodynamic_load", "thermodynamic_load must not be negative."))
    if s.step_index < 0:
        issues.append(ConstraintIssue("step_index", "step_index must not be negative."))
    if len(s.memory) < 0:
        issues.append(ConstraintIssue("memory", "memory length is invalid."))

    return ConstraintReport(valid=(len(issues) == 0), issues=tuple(issues))


# ============================================================
# Invariants
# ============================================================


def enforce_invariants(s: TheoryState) -> TheoryState:
    """
    Enforce the core structural invariants of the theory.

    Invariants:
        - viability is the complement of thermodynamic load in a loose sense
        - boundary integrity and consciousness remain normalized
        - all public scores stay inside [0, 1]
        - step index is a nonnegative integer
    """
    s = sanitize_state(s)

    # Loose thermodynamic consistency: higher load means lower viability.
    s.viability = clamp(1.0 - 0.50 * s.thermodynamic_load, 0.0, 1.0)

    # High-level scores should not drift above 1 even with smoothing.
    s.boundary_integrity = clamp(s.boundary_integrity, 0.0, 1.0)
    s.consciousness_index = clamp(s.consciousness_index, 0.0, 1.0)
    s.subjective_experience = clamp(s.subjective_experience, 0.0, 1.0)
    s.global_integration = clamp(s.global_integration, 0.0, 1.0)

    # Memory is allowed to grow only as later modules permit.
    s.step_index = int(max(0, s.step_index))
    return s


# ============================================================
# Convenience helpers
# ============================================================


def check_all(x: TheoryInputs, s: TheoryState) -> Tuple[ConstraintReport, ConstraintReport]:
    """Validate inputs and state together."""
    return validate_inputs(x), validate_state(s)
