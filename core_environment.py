#!/usr/bin/env python3
"""
core_environment.py

Upgraded multi-agent environment layer for the Evolutionary Survival Theory of Consciousness.
Symmetrically links the actions of both running agents directly to the shared world state parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, List, Literal, Optional, Sequence, Tuple

from core_types import TheoryInputs


# ============================================================
# Helpers
# ============================================================


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ============================================================
# Environment modes
# ============================================================


EnvironmentMode = Literal[
    "calm",
    "stress",
    "crisis",
    "recover",
    "social",
    "scarcity",
    "volatile",
]


@dataclass(frozen=True)
class EnvironmentEvent:
    """A discrete event that changes the world state."""

    name: str
    stress_delta: float = 0.0
    scarcity_delta: float = 0.0
    volatility_delta: float = 0.0
    social_pressure_delta: float = 0.0
    uncertainty_delta: float = 0.0
    recovery_delta: float = 0.0


@dataclass
class EnvironmentState:
    """
    Persistent environment state.

    These values are normalized to [0, 1] unless otherwise noted.
    """

    step_index: int = 0
    stress: float = 0.25
    scarcity: float = 0.20
    volatility: float = 0.20
    social_pressure: float = 0.20
    uncertainty: float = 0.20
    recovery: float = 0.50
    temperature: float = 0.50
    threat_level: float = 0.20
    opportunity_level: float = 0.50
    mode: EnvironmentMode = "calm"
    history: List[Dict[str, float]] = field(default_factory=list)


# ============================================================
# Default dynamics
# ============================================================


@dataclass(frozen=True)
class EnvironmentDynamics:
    """Tunable parameters for world evolution."""

    stress_decay: float = 0.06
    volatility_decay: float = 0.04
    scarcity_decay: float = 0.03
    social_pressure_decay: float = 0.03
    uncertainty_decay: float = 0.04
    recovery_growth: float = 0.03

    stress_noise: float = 0.05
    volatility_noise: float = 0.05
    scarcity_noise: float = 0.04
    social_noise: float = 0.03
    uncertainty_noise: float = 0.04

    crisis_stress_boost: float = 0.25
    crisis_volatility_boost: float = 0.20
    crisis_social_boost: float = 0.15
    crisis_uncertainty_boost: float = 0.20

    calm_stress_drop: float = 0.10
    calm_recovery_boost: float = 0.08

    scarcity_boost: float = 0.20
    social_boost: float = 0.20
    volatile_boost: float = 0.18

    history_limit: int = 256


# ============================================================
# Core environment logic
# ============================================================


class EnvironmentEngine:
    """
    Generates the world conditions that feed the theory inputs.

    The update order is:
        1. Apply mode/event effects
        2. Process symmetric multi-agent action impacts
        3. Drift toward baseline
        4. Add controlled noise
        5. Derive threat/opportunity
        6. Emit TheoryInputs for the core engine
    """

    def __init__(self, dynamics: Optional[EnvironmentDynamics] = None, seed: Optional[int] = None):
        self.dynamics = dynamics or EnvironmentDynamics()
        self.state = EnvironmentState()
        self.rng = random.Random(seed)

    # --------------------------------------------------------
    # State mutation
    # --------------------------------------------------------

    def set_mode(self, mode: EnvironmentMode) -> EnvironmentState:
        self.state.mode = mode
        return self.state

    def apply_event(self, event: EnvironmentEvent) -> EnvironmentState:
        s = self.state
        s.stress = clamp(s.stress + event.stress_delta, 0.0, 1.0)
        s.scarcity = clamp(s.scarcity + event.scarcity_delta, 0.0, 1.0)
        s.volatility = clamp(s.volatility + event.volatility_delta, 0.0, 1.0)
        s.social_pressure = clamp(s.social_pressure + event.social_pressure_delta, 0.0, 1.0)
        s.uncertainty = clamp(s.uncertainty + event.uncertainty_delta, 0.0, 1.0)
        s.recovery = clamp(s.recovery + event.recovery_delta, 0.0, 1.0)
        self._derive_secondary()
        return s

    def step(
        self, 
        mode: Optional[EnvironmentMode] = None, 
        event: Optional[EnvironmentEvent] = None,
        action_a: str = "",
        action_b: str = ""
    ) -> EnvironmentState:
        """Advance the environment by one tick, factoring in dual agent interactions."""
        s = self.state
        d = self.dynamics
        s.step_index += 1

        if mode is not None:
            s.mode = mode

        # 1) Mode effects
        if s.mode == "calm":
            s.stress -= d.calm_stress_drop
            s.recovery += d.calm_recovery_boost
            s.volatility -= 0.02
            s.uncertainty -= 0.02
        elif s.mode == "stress":
            s.stress += 0.10
            s.volatility += 0.05
            s.uncertainty += 0.05
        elif s.mode == "crisis":
            s.stress += d.crisis_stress_boost
            s.volatility += d.crisis_volatility_boost
            s.social_pressure += d.crisis_social_boost
            s.uncertainty += d.crisis_uncertainty_boost
        elif s.mode == "recover":
            s.stress -= 0.14
            s.recovery += 0.12
            s.volatility -= 0.03
            s.uncertainty -= 0.03
        elif s.mode == "social":
            s.social_pressure += d.social_boost
            s.uncertainty += 0.04
            s.volatility += 0.03
        elif s.mode == "scarcity":
            s.scarcity += d.scarcity_boost
            s.stress += 0.08
            s.uncertainty += 0.05
        elif s.mode == "volatile":
            s.volatility += d.volatile_boost
            s.stress += 0.06
            s.uncertainty += 0.08

        # 2) External event
        if event is not None:
            self.apply_event(event)

        # 2.5) SYMMETRIC MULTI-AGENT ACTION IMPACTS
        # Parse active tokens to directly modify environmental bounds before noise handles them.
        clean_a = action_a.split()[0].lower() if action_a else ""
        clean_b = action_b.split()[0].lower() if action_b else ""
        
        for action in [clean_a, clean_b]:
            if action == "explore":
                s.scarcity += 0.12        # High exploitation drains environmental resource density
                s.uncertainty -= 0.03     # Active mapping clears away local unknowns
            elif action in {"coordinate", "bond", "support"}:
                s.social_pressure -= 0.05 # Cooperative interactions damp relational stress
                s.stress -= 0.03          # Prosocial co-regulation reduces baseline threat
                s.scarcity += 0.02        # Highly efficient resource consumption signature
            elif action in {"threaten", "isolate", "reject"}:
                s.social_pressure += 0.18 # Aggressive posturing spikes the social tension matrix
                s.stress += 0.10          # Hostility fractures safety bounds
                s.uncertainty += 0.04     # Conflict destabilizes predictive environments
            elif action in {"defend", "hide"}:
                s.scarcity += 0.01        # Minimal resource drain signature under preservation postures

        # 3) Drift and noise
        s.stress += self.rng.uniform(-d.stress_noise, d.stress_noise)
        s.volatility += self.rng.uniform(-d.volatility_noise, d.volatility_noise)
        s.scarcity += self.rng.uniform(-d.scarcity_noise, d.scarcity_noise)
        s.social_pressure += self.rng.uniform(-d.social_noise, d.social_noise)
        s.uncertainty += self.rng.uniform(-d.uncertainty_noise, d.uncertainty_noise)

        s.stress -= d.stress_decay * (s.stress - 0.25)
        s.volatility -= d.volatility_decay * (s.volatility - 0.20)
        s.scarcity -= d.scarcity_decay * (s.scarcity - 0.20)
        s.social_pressure -= d.social_pressure_decay * (s.social_pressure - 0.20)
        s.uncertainty -= d.uncertainty_decay * (s.uncertainty - 0.20)
        s.recovery += d.recovery_growth * (0.50 - s.recovery)

        # 4) Clamp and derive secondary variables
        self._clamp_primary()
        self._derive_secondary()

        # 5) Record history
        self._store_history()
        return s

    # --------------------------------------------------------
    # Derived values
    # --------------------------------------------------------

    def _clamp_primary(self) -> None:
        s = self.state
        s.stress = clamp(s.stress, 0.0, 1.0)
        s.scarcity = clamp(s.scarcity, 0.0, 1.0)
        s.volatility = clamp(s.volatility, 0.0, 1.0)
        s.social_pressure = clamp(s.social_pressure, 0.0, 1.0)
        s.uncertainty = clamp(s.uncertainty, 0.0, 1.0)
        s.recovery = clamp(s.recovery, 0.0, 1.0)

    def _derive_secondary(self) -> None:
        s = self.state
        # Threat rises with stress, scarcity, volatility, and social pressure.
        s.threat_level = clamp(
            0.35 * s.stress + 0.25 * s.scarcity + 0.20 * s.volatility + 0.20 * s.social_pressure,
            0.0,
            1.0,
        )
        # Opportunity rises with recovery and lower threat.
        s.opportunity_level = clamp(0.60 * s.recovery + 0.40 * (1.0 - s.threat_level), 0.0, 1.0)
        # Temperature is a simple blended environmental intensity proxy.
        s.temperature = clamp(0.50 * s.stress + 0.30 * s.volatility + 0.20 * s.uncertainty, 0.0, 1.0)

    # --------------------------------------------------------
    # Theory input emission
    # --------------------------------------------------------

    def to_inputs(
        self,
        memory_depth: float = 0.0,
        self_consistency: float = 0.5,
        prediction_target: float = 0.5,
        observed_state: float = 0.5,
        language_support: float = 0.0,
        action_cost: float = 0.0,
    ) -> TheoryInputs:
        """
        Convert the current world into theory inputs.

        Later modules can customize which parts of the environment map into
        prediction, social threat, uncertainty, and action cost.
        """
        s = self.state
        return TheoryInputs(
            homeostatic_deviation=s.threat_level,
            environmental_stress=s.stress,
            prediction_target=prediction_target,
            observed_state=observed_state,
            social_threat=s.social_pressure,
            social_support=s.opportunity_level,
            language_support=language_support,
            action_cost=action_cost,
            memory_depth=memory_depth,
            self_consistency=self_consistency,
            external_uncertainty=s.uncertainty,
        )

    # --------------------------------------------------------
    # Convenience accessors
    # --------------------------------------------------------

    def snapshot(self) -> Dict[str, float]:
        s = self.state
        return {
            "step_index": float(s.step_index),
            "stress": s.stress,
            "scarcity": s.scarcity,
            "volatility": s.volatility,
            "social_pressure": s.social_pressure,
            "uncertainty": s.uncertainty,
            "recovery": s.recovery,
            "temperature": s.temperature,
            "threat_level": s.threat_level,
            "opportunity_level": s.opportunity_level,
        }

    def _store_history(self) -> None:
        s = self.state
        s.history.append(self.snapshot())
        s.history = s.history[-self.dynamics.history_limit :]

    def recent_history(self, n: int = 5) -> List[Dict[str, float]]:
        return self.state.history[-max(0, n) :]


# ============================================================
# Preset event library
# ============================================================


PRESET_EVENTS: Dict[str, EnvironmentEvent] = {
    "alarm": EnvironmentEvent(name="alarm", stress_delta=0.10, volatility_delta=0.08, uncertainty_delta=0.06),
    "food_abundance": EnvironmentEvent(name="food_abundance", scarcity_delta=-0.20, recovery_delta=0.10),
    "predator": EnvironmentEvent(name="predator", stress_delta=0.20, volatility_delta=0.15, uncertainty_delta=0.10),
    "social_bond": EnvironmentEvent(name="social_bond", social_pressure_delta=-0.10, recovery_delta=0.08),
    "rejection": EnvironmentEvent(name="rejection", social_pressure_delta=0.15, stress_delta=0.08, uncertainty_delta=0.05),
    "scarcity_crisis": EnvironmentEvent(name="scarcity_crisis", scarcity_delta=0.25, stress_delta=0.10, uncertainty_delta=0.08),
    "stabilize": EnvironmentEvent(name="stabilize", stress_delta=-0.12, volatility_delta=-0.08, uncertainty_delta=-0.05, recovery_delta=0.10),
}


def get_event(name: str) -> EnvironmentEvent:
    if name not in PRESET_EVENTS:
        raise KeyError(f"Unknown event: {name}")
    return PRESET_EVENTS[name]