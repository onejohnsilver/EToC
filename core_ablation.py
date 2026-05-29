#!/usr/bin/env python3
"""
core_ablation.py

Ablation layer for the Evolutionary Survival Theory of Consciousness.

This file provides a clean way to turn theory layers on and off.
It does not redefine the theory equations.
It simply controls which layers are allowed to contribute.

Primary purpose:
    - test survival-only vs deeper theory layers
    - isolate the effect of recursion, social modeling, self-model depth, etc.
    - support later experiments and performance comparisons
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

from core_types import LayerName, TheoryConfig, TheoryInputs, TheoryState


# ============================================================
# Ablation configuration
# ============================================================


@dataclass(frozen=True)
class AblationConfig:
    """
    Controls which layers are active.

    A layer is considered active unless it appears in disabled_layers.
    """

    disabled_layers: Tuple[LayerName, ...] = ()

    def is_enabled(self, layer: LayerName) -> bool:
        return layer not in self.disabled_layers

    def enabled_layers(self, all_layers: Iterable[LayerName]) -> Tuple[LayerName, ...]:
        return tuple(layer for layer in all_layers if self.is_enabled(layer))


@dataclass(frozen=True)
class AblationPreset:
    """
    Named ablation preset.

    This helps later simulation files quickly swap architectures.
    """

    name: str
    config: AblationConfig
    description: str = ""


# ============================================================
# Presets
# ============================================================


DEFAULT_LAYERS: Tuple[LayerName, ...] = (
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


PRESETS: Dict[str, AblationPreset] = {
    "full_theory": AblationPreset(
        name="full_theory",
        config=AblationConfig(disabled_layers=()),
        description="All layers active.",
    ),
    "survival_only": AblationPreset(
        name="survival_only",
        config=AblationConfig(
            disabled_layers=(
                "boundary",
                "prediction",
                "affect",
                "self_model",
                "social_model",
                "recursion",
                "subjective_experience",
                "consciousness",
            )
        ),
        description="Only the base survival layer is active.",
    ),
    "no_recursion": AblationPreset(
        name="no_recursion",
        config=AblationConfig(disabled_layers=("recursion",)),
        description="Turns off recursive integration.",
    ),
    "no_social": AblationPreset(
        name="no_social",
        config=AblationConfig(disabled_layers=("social_model",)),
        description="Turns off social modeling.",
    ),
    "no_self_model": AblationPreset(
        name="no_self_model",
        config=AblationConfig(disabled_layers=("self_model",)),
        description="Turns off self-model depth.",
    ),
    "no_affect": AblationPreset(
        name="no_affect",
        config=AblationConfig(disabled_layers=("affect",)),
        description="Turns off affective valuation.",
    ),
    "no_prediction": AblationPreset(
        name="no_prediction",
        config=AblationConfig(disabled_layers=("prediction",)),
        description="Turns off prediction and prediction error contribution.",
    ),
    "no_consciousness": AblationPreset(
        name="no_consciousness",
        config=AblationConfig(disabled_layers=("subjective_experience", "consciousness")),
        description="Turns off subjective experience and final consciousness score.",
    ),
    "no_language": AblationPreset(
        name="no_language",
        config=AblationConfig(disabled_layers=("recursion", "subjective_experience", "consciousness")),
        description="Removes language-supported recursive stabilization effects in downstream layers.",
    ),
}


# ============================================================
# Layer utilities
# ============================================================


def normalize_layer_name(name: str) -> LayerName:
    """Convert a string to a known layer name if possible."""
    aliases = {
        "self": "self_model",
        "social": "social_model",
        "experience": "subjective_experience",
        "conscious": "consciousness",
    }
    name = aliases.get(name, name)
    if name not in DEFAULT_LAYERS:
        raise ValueError(f"Unknown layer name: {name}")
    return name  # type: ignore[return-value]


def make_disabled(*layers: str) -> AblationConfig:
    """Create an ablation config from a variable number of layer names."""
    disabled = tuple(normalize_layer_name(layer) for layer in layers)
    return AblationConfig(disabled_layers=disabled)


def active_layers_from_config(config: AblationConfig, config_template: TheoryConfig | None = None) -> Tuple[LayerName, ...]:
    """
    Return the active layer set in theory order.

    Later code can use this to determine which transforms are allowed to run.
    """
    ordered = config_template.enabled_layers if config_template is not None else DEFAULT_LAYERS
    return config.enabled_layers(ordered)


# ============================================================
# State masking
# ============================================================


def zero_state_fields(state: TheoryState, layers: Iterable[LayerName]) -> TheoryState:
    """
    Return a copy of state with selected layer-derived fields zeroed out.

    This is useful for ablation comparisons after a run.
    """
    disabled = set(layers)
    s = TheoryState(
        viability=state.viability,
        boundary_integrity=(0.0 if "boundary" in disabled else state.boundary_integrity),
        thermodynamic_load=state.thermodynamic_load,
        survival_loss=(0.0 if "survival" in disabled else state.survival_loss),
        prediction_error=(0.0 if "prediction" in disabled else state.prediction_error),
        predictive_precision=(0.0 if "prediction" in disabled else state.predictive_precision),
        affect_valence=(0.0 if "affect" in disabled else state.affect_valence),
        affect_arousal=(0.0 if "affect" in disabled else state.affect_arousal),
        self_model_depth=(0.0 if "self_model" in disabled else state.self_model_depth),
        social_model_depth=(0.0 if "social_model" in disabled else state.social_model_depth),
        recursive_integration=(0.0 if "recursion" in disabled else state.recursive_integration),
        language_stability=(0.0 if "subjective_experience" in disabled else state.language_stability),
        subjective_experience=(0.0 if "subjective_experience" in disabled else state.subjective_experience),
        consciousness_index=(0.0 if "consciousness" in disabled else state.consciousness_index),
        global_integration=(0.0 if "subjective_experience" in disabled else state.global_integration),
        step_index=state.step_index,
        memory=[*state.memory],
    )
    return s


# ============================================================
# Input masking
# ============================================================


def zero_inputs_for_ablation(inputs: TheoryInputs, layers: Iterable[LayerName]) -> TheoryInputs:
    """
    Return a masked input view for a given ablation.

    This does not change the theory itself; it just removes the evidence that
    would feed a disabled layer.
    """
    disabled = set(layers)
    return TheoryInputs(
        homeostatic_deviation=inputs.homeostatic_deviation,
        environmental_stress=inputs.environmental_stress,
        prediction_target=(0.5 if "prediction" in disabled else inputs.prediction_target),
        observed_state=(0.5 if "prediction" in disabled else inputs.observed_state),
        social_threat=(0.0 if "social_model" in disabled else inputs.social_threat),
        social_support=(0.0 if "social_model" in disabled else inputs.social_support),
        language_support=(0.0 if "subjective_experience" in disabled else inputs.language_support),
        action_cost=inputs.action_cost,
        memory_depth=(0.0 if "recursion" in disabled else inputs.memory_depth),
        self_consistency=(0.5 if "self_model" in disabled else inputs.self_consistency),
        external_uncertainty=inputs.external_uncertainty,
        peer_prediction_accuracy=(0.5 if "social_model" in disabled else inputs.peer_prediction_accuracy),
    )


# ============================================================
# Preset helpers
# ============================================================


def get_preset(name: str) -> AblationPreset:
    """Fetch a named ablation preset."""
    if name not in PRESETS:
        raise KeyError(f"Unknown preset: {name}")
    return PRESETS[name]


def list_presets() -> List[str]:
    return list(PRESETS.keys())


def describe_preset(name: str) -> str:
    preset = get_preset(name)
    active = active_layers_from_config(preset.config)
    disabled = preset.config.disabled_layers
    return (
        f"{preset.name}: {preset.description}\n"
        f"  active={active}\n"
        f"  disabled={disabled}"
    )


# ============================================================
# Convenience comparison helpers
# ============================================================


def compare_configs(a: AblationConfig, b: AblationConfig) -> Dict[str, Tuple[bool, bool]]:
    """Compare two ablation configs layer by layer."""
    out: Dict[str, Tuple[bool, bool]] = {}
    for layer in DEFAULT_LAYERS:
        out[layer] = (a.is_enabled(layer), b.is_enabled(layer))
    return out
