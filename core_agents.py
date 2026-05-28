#!/usr/bin/env python3
"""
core_agents.py

Agent layer for the Evolutionary Survival Theory of Consciousness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional, Sequence, Tuple

from core_types import TheoryConfig, TheoryInputs, TheoryState, TheoryWeights
from core_math import compute_all, TheoryMathOutput
from core_constraints import enforce_invariants, sanitize_inputs, sanitize_state
from core_memory import MemoryManager, MemoryTrace
from core_environment import EnvironmentEngine, EnvironmentMode


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass(frozen=True)
class AgentProfile:
    """Structural agent profile defining theory layer emphasis settings."""
    name: str
    reactive: bool = False
    active_inference: bool = False
    social_depth_bias: float = 0.0
    recursion_bias: float = 0.0
    self_model_bias: float = 0.0
    language_bias: float = 0.0
    threat_sensitivity: float = 1.0
    support_sensitivity: float = 1.0
    memory_span: int = 32


PROFILES: Dict[str, AgentProfile] = {
    "reactive": AgentProfile(
        name="reactive", reactive=True, social_depth_bias=-0.10, recursion_bias=-0.15,
        self_model_bias=-0.10, language_bias=-0.15, threat_sensitivity=1.20,
        support_sensitivity=0.80, memory_span=16,
    ),
    "recursive": AgentProfile(
        name="recursive", reactive=False, social_depth_bias=0.10, recursion_bias=0.25,
        self_model_bias=0.20, language_bias=0.15, threat_sensitivity=1.00,
        support_sensitivity=1.00, memory_span=48,
    ),
    "social": AgentProfile(
        name="social", reactive=False, social_depth_bias=0.30, recursion_bias=0.10,
        self_model_bias=0.10, language_bias=0.20, threat_sensitivity=0.95,
        support_sensitivity=1.20, memory_span=48,
    ),
    "hybrid": AgentProfile(
        name="hybrid", reactive=False, social_depth_bias=0.20, recursion_bias=0.20,
        self_model_bias=0.20, language_bias=0.20, threat_sensitivity=1.00,
        support_sensitivity=1.00, memory_span=64,
    ),
    "active_inf": AgentProfile(
        name="active_inf", reactive=False, active_inference=True, social_depth_bias=0.15,
        recursion_bias=0.20, self_model_bias=0.25, language_bias=0.10,
        threat_sensitivity=1.00, support_sensitivity=1.10, memory_span=48,
    ),
}


@dataclass
class AgentState:
    """Persistent agent state sitting on top of the mathematical theory core."""
    name: str
    profile: AgentProfile
    engine_state: TheoryState = field(default_factory=TheoryState)
    memory: MemoryManager = field(default_factory=MemoryManager)

    trust_in_user: float = 0.50
    trust_in_other: float = 0.50
    attachment: float = 0.50
    caution: float = 0.50
    curiosity: float = 0.50
    confidence: float = 0.50
    mood: float = 0.50

    last_action: str = "idle"
    last_report: str = ""
    dialogue_history: List[str] = field(default_factory=list)


class MirrorLayer:
    """Tracks an internal shadow-model of a peer agent to calculate social prediction error."""
    def __init__(self, target_name: str):
        self.target_name = target_name
        self.estimated_stress = 0.25
        self.estimated_caution = 0.50
        self.social_prediction_error = 0.0
        self.predicted_action = "wait"

    def predict_peer_action(self) -> str:
        if self.estimated_stress > 0.60:
            return "withdraw" if self.estimated_caution > 0.60 else "defend"
        return "bond" if self.estimated_stress < 0.30 else "explore"

    def update_shadow_model(self, actual_action: str, env_stress: float):
        clean_actual = actual_action.split()[0].lower() if actual_action else "wait"
        
        if clean_actual == self.predicted_action:
            self.social_prediction_error = max(0.0, self.social_prediction_error - 0.05)
        else:
            self.social_prediction_error = min(1.0, self.social_prediction_error + 0.20)
            
        if clean_actual in {"defend", "withdraw", "hide", "isolate", "threaten"}:
            self.estimated_stress = min(1.0, self.estimated_stress + 0.15)
            self.estimated_caution = min(1.0, self.estimated_caution + 0.10)
        elif clean_actual in {"bond", "support", "coordinate", "signal"}:
            self.estimated_stress = max(0.0, self.estimated_stress - 0.10)
            self.estimated_caution = max(0.0, self.estimated_caution - 0.08)
            
        self.estimated_stress = min(1.0, self.estimated_stress + (env_stress * 0.05))
        self.predicted_action = self.predict_peer_action()


class AgentEngine:
    """Agent wrapper linking operational profiles to the math computational core."""

    def __init__(
        self,
        name: str,
        profile_name: str = "hybrid",
        weights: Optional[TheoryWeights] = None,
        config: Optional[TheoryConfig] = None,
        seed: Optional[int] = None,
    ):
        if profile_name not in PROFILES:
            raise KeyError(f"Unknown profile: {profile_name}")
        self.profile = PROFILES[profile_name]
        self.name = name
        self.weights = weights or TheoryWeights()
        self.config = config or TheoryConfig(memory_limit=self.profile.memory_span)
        self.state = AgentState(name=name, profile=self.profile)
        self.rng = random.Random(seed)
        self.mirror: Optional[MirrorLayer] = None

    def build_inputs(
        self,
        environment: EnvironmentEngine,
        observed_state: float = 0.5,
        prediction_target: float = 0.5,
        action_cost: float = 0.0,
        social_signal: float = 0.0,
        language_support: float = 0.0,
    ) -> TheoryInputs:
        env = environment.state
        
        # 1. Capture base environmental forces
        raw_threat = clamp(env.social_pressure * self.profile.threat_sensitivity, 0.0, 1.0)
        raw_stress = env.stress
        
        # 2. THE SOMATIC SHIELD: Translate cognitive intent into physical boundary protection
        clean_action = self.state.last_action.split()[0].lower() if self.state.last_action else ""
        
        if clean_action == "defend":
            # Defending structurally blunts direct social threats and caps environmental stress damage
            raw_threat *= 0.40  # 60% threat reduction
            raw_stress *= 0.60  # 40% stress reduction
        elif clean_action == "withdraw":
            # Withdrawing creates distance, dropping stress significantly but not stopping direct targeted threats as well
            raw_threat *= 0.70  # 30% threat reduction
            raw_stress *= 0.30  # 70% stress reduction
        elif clean_action == "hide":
            # Hiding breaks line of sight, neutralizing social threat targeting
            raw_threat *= 0.10  # 90% threat reduction
            raw_stress *= 0.80  # 20% stress reduction

        # 3. Calculate remaining parameters
        support = clamp(env.opportunity_level * self.profile.support_sensitivity, 0.0, 1.0)
        memory_depth = clamp(len(self.state.memory.bank.traces) / max(1, self.profile.memory_span), 0.0, 1.0)
        self_consistency = clamp(self.state.engine_state.self_model_depth + self.profile.self_model_bias, 0.0, 1.0)
        lang = clamp(language_support + self.profile.language_bias, 0.0, 1.0)

        # 4. Return shielded inputs to the mathematical core
        return TheoryInputs(
            homeostatic_deviation=env.threat_level,
            environmental_stress=clamp(raw_stress, 0.0, 1.0),
            prediction_target=prediction_target,
            observed_state=observed_state,
            social_threat=clamp(raw_threat + social_signal, 0.0, 1.0),
            social_support=support,
            language_support=lang,
            action_cost=action_cost,
            memory_depth=memory_depth,
            self_consistency=self_consistency,
            external_uncertainty=env.uncertainty,
        )

    def perceive_and_update(self, inputs: TheoryInputs, note: str = "") -> TheoryState:
        clean_inputs = sanitize_inputs(inputs)
        self.state.engine_state = sanitize_state(self.state.engine_state)

        output: TheoryMathOutput = compute_all(clean_inputs, self.weights)

        s = self.state.engine_state
        s.viability = clamp(0.75 * s.viability + 0.25 * (1.0 - 0.50 * output.survival_loss), 0.0, 1.0)
        s.boundary_integrity = output.boundary_integrity
        s.thermodynamic_load = 0.75 * s.thermodynamic_load + 0.25 * output.survival_loss
        s.survival_loss = output.survival_loss
        s.prediction_error = output.prediction_error
        s.predictive_precision = output.predictive_precision
        s.affect_valence = output.affect_valence
        s.affect_arousal = output.affect_arousal
        s.self_model_depth = output.self_model_depth
        s.social_model_depth = output.social_model_depth
        s.recursive_integration = output.recursive_integration
        s.language_stability = clean_inputs.language_support
        s.subjective_experience = output.subjective_experience
        s.consciousness_index = output.consciousness_index
        s.global_integration = output.global_integration
        s.step_index += 1

        self.state.engine_state = enforce_invariants(s)
        self.state.memory.store(self.state.engine_state, note=note)
        self.state.engine_state.memory = self.state.memory.export_state_memory()
        return self.state.engine_state

    def update_attitudes(self, user_action: str, other_agent_action: str, env_stress: float) -> None:
        s = self.state
        if "help" in user_action or "feed" in user_action:
            s.trust_in_user = clamp(s.trust_in_user + 0.08, 0.0, 1.0)
            s.mood = clamp(s.mood + 0.06, 0.0, 1.0)
        if "threaten" in user_action or "isolate" in user_action:
            s.trust_in_user = clamp(s.trust_in_user - 0.12, 0.0, 1.0)
            s.caution = clamp(s.caution + 0.10, 0.0, 1.0)
        if "ignore" in user_action:
            s.trust_in_user = clamp(s.trust_in_user - 0.04, 0.0, 1.0)

        if other_agent_action in {"bond", "seek_alliance", "help", "protect"}:
            s.trust_in_other = clamp(s.trust_in_other + 0.05, 0.0, 1.0)
            s.attachment = clamp(s.attachment + 0.04, 0.0, 1.0)
        if other_agent_action in {"withdraw", "cautious", "reject", "isolate"}:
            s.trust_in_other = clamp(s.trust_in_other - 0.05, 0.0, 1.0)
            s.caution = clamp(s.caution + 0.04, 0.0, 1.0)

        s.caution = clamp(s.caution + 0.05 * env_stress, 0.0, 1.0)
        s.confidence = clamp(s.confidence - 0.03 * env_stress + 0.02 * s.engine_state.consciousness_index, 0.0, 1.0)
        s.curiosity = clamp(s.curiosity + 0.01 * (1.0 - env_stress), 0.0, 1.0)

    def choose_action(self) -> str:
        s = self.state
        eng = s.engine_state

        if getattr(self.profile, "active_inference", False):
            candidates = ["wait", "explore", "conserve", "withdraw", "defend", "hide"]
            if not self.profile.reactive:
                candidates += ["plan", "reappraise", "model_self", "bond", "support", "reflect"]

            cost_map = {
                "wait": 0.02, "observe": 0.02, "explore": 0.08, "plan": 0.10,
                "reappraise": 0.06, "model_self": 0.08, "signal": 0.04, "coordinate": 0.06,
                "bond": 0.05, "support": 0.06, "negotiate": 0.07, "seek": 0.05,
                "seek_alliance": 0.08, "conserve": 0.03, "withdraw": 0.02, "defend": 0.07,
                "hide": 0.05, "reflect": 0.05
            }

            best_action = "wait"
            min_efe = float("inf")
            somatic_distress = max(eng.survival_loss, eng.thermodynamic_load)

            for act in candidates:
                cost = cost_map.get(act, 0.05)
                expected_error = eng.prediction_error
                expected_loss = eng.survival_loss

                if act in {"withdraw", "hide", "defend"}:
                    if eng.survival_loss > 0.4:
                        expected_loss -= 0.15 * (1.0 + s.caution)
                
                elif act in {"bond", "support"}:
                    if eng.social_model_depth > 0.4:
                        social_premium = 0.10 * s.attachment
                        if somatic_distress > 0.3:
                            social_premium *= max(0.0, 1.0 - ((somatic_distress - 0.3) / 0.5))
                        expected_error -= social_premium
                    if somatic_distress > 0.3:
                        cost += somatic_distress * 0.15

                elif act in {"plan", "model_self"}:
                    if eng.recursive_integration > 0.4:
                        reflect_premium = 0.05 * s.curiosity
                        if somatic_distress > 0.5:
                            reflect_premium *= max(0.0, 1.0 - ((somatic_distress - 0.5) / 0.5))
                            cost += 0.05
                        expected_error -= reflect_premium

                elif act == "conserve":
                    if eng.thermodynamic_load > 0.5:
                        expected_loss -= 0.10 * (1.0 + somatic_distress)

                # NEW: Crisis Probing Bonus
                # If the agent is in a catastrophe (somatic_distress > 0.7), 
                # reward actions that resolve uncertainty rather than just waiting.
                if somatic_distress > 0.7:
                    if act in {"explore", "coordinate", "defend", "signal"}:
                        cost -= 0.10 * (somatic_distress - 0.7)

                efe = clamp(expected_error, 0.0, 1.0) + clamp(expected_loss, 0.0, 1.0) + cost
                if efe < min_efe:
                    min_efe = efe
                    best_action = act
            return best_action

        # Clean, Deduplicated Baseline Fallback Policies
        if self.profile.reactive:
            if eng.survival_loss > 0.75 or eng.affect_arousal > 0.70:
                return self.rng.choice(["withdraw", "defend", "hide"])
            if eng.social_model_depth > 0.55:
                return self.rng.choice(["seek", "bond"])
            return self.rng.choice(["wait", "explore"])

        if eng.survival_loss > 0.80:
            return "seek_alliance" if s.trust_in_other > 0.55 else "conserve"
        if eng.social_model_depth > 0.60 and s.attachment > 0.50:
            return self.rng.choice(["bond", "support", "negotiate"])
        if eng.recursive_integration > 0.55:
            return self.rng.choice(["plan", "reappraise", "model_self"])
        if eng.consciousness_index > 0.55:
            return self.rng.choice(["reflect", "signal", "coordinate"])
        return self.rng.choice(["explore", "observe", "wait"])

    def generate_report(self) -> str:
        s = self.state.engine_state
        idn = self.state.memory.identity_summary()
        report = (
            f"{self.name}: loss={s.survival_loss:.3f}, boundary={s.boundary_integrity:.3f}, "
            f"self={s.self_model_depth:.3f}, social={s.social_model_depth:.3f}, "
            f"recursion={s.recursive_integration:.3f}, conc={s.consciousness_index:.3f}, "
            f"identity={idn.identity_stability:.3f}"
        )
        self.state.last_report = report
        return report

    def speak(self) -> str:
        s = self.state.engine_state
        if getattr(self.profile, "active_inference", False):
            msg = f"System executing closed-loop active inference. Strategy footprint: {self.state.last_action.upper()}"
        elif self.profile.reactive:
            msg = "I need safety now." if s.survival_loss > 0.75 else "Something is happening." if s.affect_arousal > 0.65 else "I am waiting."
        else:
            if s.recursive_integration > 0.60:
                msg = "I am updating my model of myself and others."
            elif s.social_model_depth > 0.60:
                msg = "I am tracking social risk and attachment."
            elif s.subjective_experience > 0.55:
                msg = "I feel the state shifting."
            else:
                msg = "I am observing the world." 
        self.state.dialogue_history.append(msg)
        self.state.dialogue_history = self.state.dialogue_history[-64:]
        return msg

    def snapshot(self) -> Dict[str, float]:
        s = self.state
        eng = s.engine_state
        base_snap = {
            "name": float(hash(self.name) % 1000000),
            "viability": eng.viability,
            "boundary_integrity": eng.boundary_integrity,
            "thermodynamic_load": eng.thermodynamic_load,
            "survival_loss": eng.survival_loss,
            "prediction_error": eng.prediction_error,
            "predictive_precision": eng.predictive_precision,
            "affect_valence": eng.affect_valence,
            "affect_arousal": eng.affect_arousal,
            "self_model_depth": eng.self_model_depth,
            "social_model_depth": eng.social_model_depth,
            "recursive_integration": eng.recursive_integration,
            "consciousness_index": eng.consciousness_index,
            "confidence": s.confidence,
            "mood": s.mood,
        }
        if self.mirror:
            base_snap["tom_social_pe"] = self.mirror.social_prediction_error
            base_snap["tom_estimated_peer_stress"] = self.mirror.estimated_stress
            base_snap["tom_estimated_peer_caution"] = self.mirror.estimated_caution
        else:
            base_snap.update({"tom_social_pe": 0.0, "tom_estimated_peer_stress": 0.0, "tom_estimated_peer_caution": 0.0})
        return base_snap

    def recent_memories(self, n: int = 5) -> List[MemoryTrace]:
        return self.state.memory.recent_traces(n)

    def reset(self) -> None:
        self.state = AgentState(name=self.name, profile=self.profile)


def make_agent(name: str, profile_name: str = "hybrid", seed: Optional[int] = None) -> AgentEngine:
    return AgentEngine(name=name, profile_name=profile_name, seed=seed)


def make_pair(seed: Optional[int] = None) -> Tuple[AgentEngine, AgentEngine]:
    a = AgentEngine(name="A", profile_name="active_inf", seed=seed)
    b = AgentEngine(name="B", profile_name="recursive", seed=None if seed is None else seed + 1)
    a.mirror = MirrorLayer(target_name="B")
    b.mirror = MirrorLayer(target_name="A")
    return a, b