#!/usr/bin/env python3
"""
core_types.py

Vocabulary layer for the Evolutionary Survival Theory of Consciousness.

This file defines the shared data structures only.
It does not compute equations, run simulations, or update state.
Every later file should import these types and build on them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Tuple


LayerName = Literal[
    "survival",
    "boundary",
    "prediction",
    "affect",
    "self_model",
    "social_model",
    "recursion",
    "subjective_experience",
    "consciousness",
]


@dataclass(frozen=True)
class TheoryInputs:
    """
    Raw observations entering the theory engine.

    These are the external / measured values that later files will transform.
    All values should usually be normalized to the range [0, 1].
    """

    homeostatic_deviation: float = 0.0
    environmental_stress: float = 0.0
    prediction_target: float = 0.5
    observed_state: float = 0.5
    social_threat: float = 0.0
    social_support: float = 0.0
    language_support: float = 0.0
    action_cost: float = 0.0
    memory_depth: float = 0.0
    self_consistency: float = 0.5
    external_uncertainty: float = 0.0


@dataclass
class TheoryWeights:
    """
    Tunable coefficients for the theory equations.

    Later files will use these values to shape the relative contribution of
    each layer. Keeping them centralized makes ablation and calibration easy.
    """

    w_homeostasis: float = 1.0
    w_environment: float = 0.8
    w_prediction_error: float = 0.9
    w_action_cost: float = 0.35
    w_social_threat: float = 0.7
    w_social_support: float = 0.45
    w_language: float = 0.35
    w_memory: float = 0.25

    w_self_from_boundary: float = 0.55
    w_self_from_prediction: float = 0.25
    w_self_from_memory: float = 0.20

    w_social_from_threat: float = 0.45
    w_social_from_support: float = 0.45
    w_social_from_language: float = 0.10

    w_recursion_self: float = 0.40
    w_recursion_social: float = 0.35
    w_recursion_language: float = 0.25

    w_subjective_affect: float = 0.30
    w_subjective_prediction: float = 0.20
    w_subjective_self: float = 0.20
    w_subjective_social: float = 0.15
    w_subjective_recursion: float = 0.15

    w_consciousness_subjective: float = 0.45
    w_consciousness_global_integration: float = 0.30
    w_consciousness_boundary: float = 0.25


@dataclass
class TheoryState:
    """
    Internal state produced by the theory engine.

    This is the persistent evolving state that later files will update.
    The fields mirror the theory's ordered layers.
    """

    viability: float = 1.0
    boundary_integrity: float = 1.0
    thermodynamic_load: float = 0.0
    survival_loss: float = 0.0

    prediction_error: float = 0.0
    predictive_precision: float = 0.5
    affect_valence: float = 0.0
    affect_arousal: float = 0.0

    self_model_depth: float = 0.2
    social_model_depth: float = 0.2
    recursive_integration: float = 0.1
    language_stability: float = 0.0

    subjective_experience: float = 0.0
    consciousness_index: float = 0.0
    global_integration: float = 0.0

    step_index: int = 0
    memory: List[Dict[str, float]] = field(default_factory=list)


@dataclass(frozen=True)
class TheoryOutput:
    """
    Optional one-step output bundle.

    Some later files may prefer returning this instead of raw dictionaries.
    """

    inputs: TheoryInputs
    state: TheoryState
    layer_order: Tuple[LayerName, ...]


@dataclass(frozen=True)
class TheoryConfig:
    """
    High-level configuration for a simulation or engine instance.

    This keeps structural choices separate from the math.
    Later files can add more knobs here without changing the core state types.
    """

    name: str = "evolutionary_survival_theory"
    version: str = "core_v1"
    enabled_layers: Tuple[LayerName, ...] = (
        "survival",
        "boundary",
        "prediction",
        "affect",
        "self_model",
        "social_model",
        "recursion",
        "subjective_experience",
        "consciousness",
    )
    memory_limit: int = 128
