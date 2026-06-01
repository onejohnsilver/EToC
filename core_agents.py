#!/usr/bin/env python3
"""
core_agents.py

Agent layer for the Evolutionary Survival Theory of Consciousness.

Operator Modifications:
    - Integrated TheoryUpdater so agents utilize Allostatic Anticipation.
    - Centralized MemoryManager inside TheoryUpdater to fix ui.py visibility.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import random
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

from core_types import LayerName, TheoryConfig, TheoryInputs, TheoryState, TheoryWeights
# OPERATOR FIX: Removed compute_all, imported TheoryUpdater
from core_update import TheoryUpdater 
from core_constraints import enforce_invariants, sanitize_inputs, sanitize_state
from core_counterfactual import CounterfactualSimulator
from core_memory import MemoryTrace
from core_environment import EnvironmentEngine, EnvironmentMode
from core_somatic import SomaticState, classify_somatic_emotion
from core_language import LanguageGenerator
from core_values import ValueSystem


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
class AdaptiveCognitiveStyle:
    """Plastic cognitive style that drifts from lived outcomes."""

    threat_sensitivity: float = 1.0
    social_depth_bias: float = 0.0
    recursion_bias: float = 0.0
    self_model_bias: float = 0.0
    trauma_load: float = 0.0
    plan_mastery: float = 0.0
    overload_streak: int = 0
    successful_plan_streak: int = 0

    @classmethod
    def from_profile(cls, profile: AgentProfile) -> "AdaptiveCognitiveStyle":
        return cls(
            threat_sensitivity=profile.threat_sensitivity,
            social_depth_bias=profile.social_depth_bias,
            recursion_bias=profile.recursion_bias,
            self_model_bias=profile.self_model_bias,
        )

    def as_dict(self) -> Dict[str, float]:
        return {
            "threat_sensitivity": self.threat_sensitivity,
            "social_depth_bias": self.social_depth_bias,
            "recursion_bias": self.recursion_bias,
            "self_model_bias": self.self_model_bias,
            "trauma_load": self.trauma_load,
            "plan_mastery": self.plan_mastery,
            "overload_streak": float(self.overload_streak),
            "successful_plan_streak": float(self.successful_plan_streak),
        }


@dataclass
class AgentState:
    """Persistent agent state sitting on top of the mathematical theory core."""
    name: str
    profile: AgentProfile
    # OPERATOR FIX: Memory is now handled entirely by the TheoryUpdater to prevent desyncs
    engine_state: TheoryState = field(default_factory=TheoryState)
    recursive_self_model: "RecursiveSelfModel" = field(default_factory=lambda: RecursiveSelfModel())
    somatic: SomaticState = field(default_factory=SomaticState)
    adaptive_style: AdaptiveCognitiveStyle = field(init=False)

    trust_in_user: float = 0.50
    trust_in_other: float = 0.50
    attachment: float = 0.50
    caution: float = 0.50
    curiosity: float = 0.50
    confidence: float = 0.50
    mood: float = 0.50

    last_action: str = "idle"
    last_utterance: str = ""
    last_report: str = ""
    last_regret: float = 0.0
    dialogue_history: List[str] = field(default_factory=list)
    value_system: ValueSystem = field(default_factory=ValueSystem)

    def __post_init__(self) -> None:
        self.adaptive_style = AdaptiveCognitiveStyle.from_profile(self.profile)
        self.curiosity = clamp(
            0.30 + 0.40 * (self.profile.recursion_bias + self.profile.language_bias) / 2.0,
            0.0,
            1.0,
        )
        self.confidence = clamp(
            0.45 + 0.20 * (1.0 - abs(self.profile.threat_sensitivity - 1.0)),
            0.0,
            1.0,
        )
        self.caution = clamp(
            0.50 + 0.30 * self.profile.threat_sensitivity - 0.15 * self.profile.support_sensitivity,
            0.0,
            1.0,
        )
        self.trust_in_user = clamp(
            0.50 + 0.15 * self.profile.support_sensitivity,
            0.0,
            1.0,
        )
        self.trust_in_other = clamp(
            0.50 + 0.10 * self.profile.support_sensitivity,
            0.0,
            1.0,
        )


@dataclass
class IntentionalFrame:
    """Hierarchical intentional structure for goal persistence and planning."""

    primary_goal: str = "maintain_safety"
    subgoals: List[str] = field(default_factory=lambda: ["shore_up_boundary", "reduce_threat"])
    active_subgoal_index: int = 0
    max_persistence: int = 6
    persistence: int = 0
    achieved: bool = False
    urgency: float = 0.0
    alignment: float = 0.5
    opportunity: float = 0.0
    rationale: str = "Maintain adaptive focus through the current situation."
    value_deficits: Dict[str, float] = field(default_factory=dict)

    def current_subgoal(self) -> str:
        if not self.subgoals:
            return self.primary_goal
        return self.subgoals[min(self.active_subgoal_index, len(self.subgoals) - 1)]

    def advance(self) -> None:
        if self.active_subgoal_index < len(self.subgoals) - 1:
            self.active_subgoal_index += 1
            self.persistence = 0
        else:
            self.achieved = True

    def reset(
        self,
        primary_goal: str,
        subgoals: List[str],
        urgency: float,
        alignment: float,
        opportunity: float,
        rationale: str,
        value_deficits: Dict[str, float],
    ) -> None:
        self.primary_goal = primary_goal
        self.subgoals = subgoals
        self.active_subgoal_index = 0
        self.max_persistence = max(4, min(10, len(subgoals) + 3))
        self.persistence = 0
        self.achieved = False
        self.urgency = clamp(urgency, 0.0, 1.0)
        self.alignment = clamp(alignment, 0.0, 1.0)
        self.opportunity = clamp(opportunity, 0.0, 1.0)
        self.rationale = rationale
        self.value_deficits = value_deficits

    def is_active(self) -> bool:
        return not self.achieved and self.persistence < self.max_persistence

    def describe(self) -> str:
        status = "active" if self.is_active() else "inactive"
        return (
            f"Primary goal: {self.primary_goal}. "
            f"Current task: {self.current_subgoal()}. "
            f"Urgency={self.urgency:.2f}, alignment={self.alignment:.2f}, persistence={self.persistence}/{self.max_persistence}. "
            f"Status: {status}."
        )


class PeerCognitiveModel:
    """Tracks a recursive social model of a peer agent for ToM predictions."""

    def __init__(self, target_name: str, recursion_depth: int = 2):
        self.target_name = target_name
        self.recursive_depth = recursion_depth
        self.estimated_stress = 0.30
        self.estimated_caution = 0.50
        self.estimated_trust = 0.50
        self.estimated_alignment = 0.50
        self.estimated_intent = "maintain_safety"
        self.estimated_emotion = "neutral"
        self.predicted_action = "wait"
        self.predicted_utterance = "I am observing the peer."
        self.prediction_error = 0.30
        self.prediction_accuracy = 0.70
        self.nested_model_depth = 1
        self.history: List[Dict[str, object]] = []

    def predict_peer_action(self) -> str:
        """Predict peer action using both history-weighted patterns and current state estimates."""
        # If we have sufficient history, weight recent patterns
        if len(self.history) >= 3:
            predicted_from_history = self._predict_from_history()
            if predicted_from_history:
                # Blend historical pattern (70%) with state-based prediction (30%)
                state_prediction = self._predict_from_state()
                # For now, prefer history when strong pattern exists
                if self.prediction_accuracy > 0.55:
                    return predicted_from_history
        
        # Fall back to state-based heuristic
        return self._predict_from_state()
    
    def _predict_from_state(self) -> str:
        """State-based heuristic prediction."""
        if self.estimated_trust > 0.65 and self.estimated_alignment > 0.55:
            if self.estimated_stress < 0.40:
                return "bond"
            if self.estimated_stress < 0.65:
                return "coordinate"
            return "support"
        if self.estimated_stress > 0.70:
            return "withdraw" if self.estimated_caution > 0.55 else "defend"
        if self.estimated_alignment > 0.50:
            return "coordinate"
        if self.estimated_trust < 0.35:
            return "withdraw"
        return "wait"
    
    def _predict_from_history(self) -> Optional[str]:
        """Learn recurring patterns from recent history with exponential recency weighting."""
        if not self.history or len(self.history) < 2:
            return None

        # Weight recent actions more heavily while scanning a larger context
        action_weights: Dict[str, float] = {}
        decay_factor = 0.85
        recent_entries = self.history[-12:]
        for i, entry in enumerate(recent_entries):  # Last 12 observations
            action = entry.get("action", "wait")
            weight = decay_factor ** (len(recent_entries) - i - 1)
            action_weights[action] = action_weights.get(action, 0.0) + weight

        # Return most frequent recent action if pattern is stronger than chance
        if action_weights:
            best_action = max(action_weights.items(), key=lambda x: x[1])[0]
            best_weight = action_weights[best_action]
            if best_weight > 1.2:
                return best_action

        return None

    def predict_peer_utterance(self) -> str:
        if self.predicted_action in {"bond", "support", "coordinate"}:
            return "I want to cooperate and keep our relationship stable."
        if self.predicted_action in {"withdraw", "defend"}:
            return "I'm concerned and need to protect my boundaries."
        if self.predicted_action == "plan":
            return "I am updating my model before deciding."
        return "I am watching the situation closely."

    def update_observation(self, actual_action: str, actual_utterance: str, env_stress: float) -> None:
        clean_action = actual_action.split()[0].lower() if actual_action else "wait"
        clean_utterance = (actual_utterance or "").lower()
        self.history.append({
            "action": clean_action,
            "utterance": clean_utterance,
            "stress": env_stress,
            "alignment": self.estimated_alignment,
            "trust": self.estimated_trust,
        })

        self._infer_from_action(clean_action, env_stress)
        self._infer_from_utterance(clean_utterance)

        if clean_action == self.predicted_action:
            self.prediction_error = max(0.0, self.prediction_error - 0.10)
        else:
            self.prediction_error = min(1.0, self.prediction_error + 0.18)

        self.prediction_accuracy = clamp(1.0 - self.prediction_error, 0.0, 1.0)
        self.nested_model_depth = min(3, max(1, int(1 + 3 * self.prediction_accuracy)))
        self.predicted_action = self.predict_peer_action()
        self.predicted_utterance = self.predict_peer_utterance()

    def _infer_from_action(self, clean_action: str, env_stress: float) -> None:
        if clean_action in {"defend", "withdraw", "hide", "isolate", "threaten"}:
            self.estimated_stress = min(1.0, self.estimated_stress + 0.14)
            self.estimated_caution = min(1.0, self.estimated_caution + 0.12)
            self.estimated_alignment = max(0.0, self.estimated_alignment - 0.08)
            self.estimated_intent = "reduce_threat"
        elif clean_action in {"bond", "support", "coordinate", "signal", "help"}:
            self.estimated_stress = max(0.0, self.estimated_stress - 0.12)
            self.estimated_caution = max(0.0, self.estimated_caution - 0.10)
            self.estimated_alignment = min(1.0, self.estimated_alignment + 0.12)
            self.estimated_trust = min(1.0, self.estimated_trust + 0.08)
            self.estimated_intent = "build_support"

        self.estimated_stress = min(1.0, self.estimated_stress + env_stress * 0.06)
        self.estimated_caution = clamp(self.estimated_caution + env_stress * 0.04, 0.0, 1.0)

    def _infer_from_utterance(self, clean_utterance: str) -> None:
        if any(keyword in clean_utterance for keyword in ["support", "cooperate", "together", "alliance"]):
            self.estimated_alignment = min(1.0, self.estimated_alignment + 0.10)
            self.estimated_trust = min(1.0, self.estimated_trust + 0.08)
            self.estimated_emotion = "affiliative"
        if any(keyword in clean_utterance for keyword in ["worry", "concern", "protect", "guard"]):
            self.estimated_stress = min(1.0, self.estimated_stress + 0.08)
            self.estimated_caution = min(1.0, self.estimated_caution + 0.06)
            self.estimated_emotion = "wary"
        if any(keyword in clean_utterance for keyword in ["think", "plan", "model", "aware"]):
            self.estimated_alignment = min(1.0, self.estimated_alignment + 0.05)
            self.estimated_emotion = "reflective"
        if "withdraw" in clean_utterance or "avoid" in clean_utterance:
            self.estimated_caution = min(1.0, self.estimated_caution + 0.08)
            self.estimated_alignment = max(0.0, self.estimated_alignment - 0.05)

    def summary(self) -> Dict[str, object]:
        return {
            "target_name": self.target_name,
            "prediction_accuracy": self.prediction_accuracy,
            "prediction_error": self.prediction_error,
            "predicted_action": self.predicted_action,
            "predicted_utterance": self.predicted_utterance,
            "estimated_stress": self.estimated_stress,
            "estimated_caution": self.estimated_caution,
            "estimated_trust": self.estimated_trust,
            "estimated_alignment": self.estimated_alignment,
            "estimated_intent": self.estimated_intent,
            "estimated_emotion": self.estimated_emotion,
            "nested_model_depth": self.nested_model_depth,
        }


class RecursiveSelfModel:
    """A metacognitive model estimating agent self-knowledge and prediction confidence."""
    def __init__(self):
        self.prediction_accuracy = 0.5
        self.narrative_coherence = 0.5
        self.intuition_reliability = 0.5
        self.meta_accuracy = 0.5
        self.level = 1

    def update(
        self,
        prediction_accuracy: float,
        narrative_coherence: float,
        intuition_reliability: float,
    ) -> None:
        self.prediction_accuracy = clamp(prediction_accuracy, 0.0, 1.0)
        self.narrative_coherence = clamp(narrative_coherence, 0.0, 1.0)
        self.intuition_reliability = clamp(intuition_reliability, 0.0, 1.0)
        self.meta_accuracy = clamp(
            0.4 * self.prediction_accuracy
            + 0.3 * self.narrative_coherence
            + 0.3 * self.intuition_reliability,
            0.0,
            1.0,
        )
        self.level = min(5, max(1, int(1 + 4 * self.meta_accuracy)))

    def summary(self) -> Dict[str, float]:
        return {
            "prediction_accuracy": self.prediction_accuracy,
            "narrative_coherence": self.narrative_coherence,
            "intuition_reliability": self.intuition_reliability,
            "meta_accuracy": self.meta_accuracy,
            "level": float(self.level),
        }


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
        self.base_weights = deepcopy(weights or TheoryWeights())
        self.weights = deepcopy(self.base_weights)
        self.config = config or TheoryConfig(memory_limit=self.profile.memory_span)
        
        self.state = AgentState(name=name, profile=self.profile)
        self.intentional_frame = IntentionalFrame()
        self.last_inputs: Optional[TheoryInputs] = None
        # OPERATOR FIX: Instantiate the Updater here so ui.py can access memory
        self.updater = TheoryUpdater(weights=self.weights, config=self.config, initial_state=self.state.engine_state)
        self.language_generator = LanguageGenerator(name=name)
        self.counterfactual = CounterfactualSimulator(weights=self.weights, config=self.config)
        
        self.rng = random.Random(seed)
        self.peer_model = PeerCognitiveModel(target_name="B" if self.name == "A" else "A")

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
        style = self.state.adaptive_style
        raw_threat = clamp(env.social_pressure * style.threat_sensitivity, 0.0, 1.0)
        raw_stress = env.stress
        
        # 2. THE SOMATIC SHIELD: Translate cognitive intent into physical boundary protection
        clean_action = self.state.last_action.split()[0].lower() if self.state.last_action else ""
        
        if clean_action == "defend":
            raw_threat *= 0.40  # 60% threat reduction
            raw_stress *= 0.60  # 40% stress reduction
        elif clean_action == "withdraw":
            raw_threat *= 0.70  # 30% threat reduction
            raw_stress *= 0.30  # 70% stress reduction
        elif clean_action == "hide":
            raw_threat *= 0.10  # 90% threat reduction
            raw_stress *= 0.80  # 20% stress reduction

        # 3. Calculate remaining parameters
        support = clamp(env.opportunity_level * self.profile.support_sensitivity + style.social_depth_bias, 0.0, 1.0)
        
        # OPERATOR FIX: Query memory depth through the updater
        memory_traces = self.updater.memory_manager.bank.traces
        memory_depth = clamp(len(memory_traces) / max(1, self.profile.memory_span), 0.0, 1.0)
        
        identity_summary = self.updater.memory_manager.identity_summary()
        identity_coherence = identity_summary.coherence if identity_summary else 0.5
        self_consistency = clamp(
            self.state.engine_state.self_model_depth + style.self_model_bias + 0.12 * identity_coherence,
            0.0,
            1.0,
        )
        lang = clamp(language_support + self.profile.language_bias, 0.0, 1.0)
        peer_accuracy = 0.5
        if self.peer_model is not None:
            peer_accuracy = clamp(self.peer_model.prediction_accuracy, 0.0, 1.0)
            support = clamp(support + 0.10 * self.peer_model.estimated_alignment, 0.0, 1.0)

        somatic = self.state.somatic
        somatic_deviation = somatic.reservoir_deviation() if hasattr(somatic, "reservoir_deviation") else 0.0

        meta_accuracy = clamp(
            0.4 * self.state.recursive_self_model.prediction_accuracy
            + 0.3 * self.state.recursive_self_model.narrative_coherence
            + 0.3 * self.state.recursive_self_model.intuition_reliability,
            0.0,
            1.0,
        )

        # 4. Return shielded inputs to the mathematical core
        return TheoryInputs(
            homeostatic_deviation=clamp(0.55 * env.threat_level + 0.45 * somatic_deviation, 0.0, 1.0),
            environmental_stress=clamp(raw_stress, 0.0, 1.0),
            prediction_target=prediction_target,
            observed_state=observed_state,
            social_threat=clamp(raw_threat + social_signal, 0.0, 1.0),
            social_support=support,
            language_support=lang,
            action_cost=action_cost,
            metabolic_reserve=somatic.metabolic_reserve,
            hydration=somatic.hydration,
            oxygenation=somatic.oxygenation,
            immune_load=somatic.immune_load,
            neural_energy=somatic.neural_energy,
            memory_depth=memory_depth,
            self_consistency=self_consistency,
            external_uncertainty=env.uncertainty,
            peer_prediction_accuracy=peer_accuracy,
            meta_accuracy=meta_accuracy,
            goal_urgency=self.intentional_frame.urgency,
            goal_alignment=self.intentional_frame.alignment,
        )

    def perceive_and_update(
        self,
        inputs: TheoryInputs,
        note: str = "",
        disabled_layers: Optional[Sequence[LayerName]] = None,
    ) -> TheoryState:
        """Route the inputs through the TheoryUpdater to activate Allostatic Anticipation."""
        clean_inputs = sanitize_inputs(inputs)
        self.last_inputs = clean_inputs
        previous_state = deepcopy(self.state.engine_state)
        previous_goal = self.intentional_frame.current_subgoal()

        # Sync the updater state with the agent's current engine state (necessary if UI injected values)
        self.updater.state = enforce_invariants(sanitize_state(self.state.engine_state))
        
        # The updater handles the math, smoothing, memory storage, and optional ablation masking.
        if disabled_layers:
            updated_state = self.updater.ablation_step(clean_inputs, disabled_layers=list(disabled_layers))
        else:
            updated_state = self.updater.step(clean_inputs)

        # Re-sync the agent's state
        self.state.engine_state = enforce_invariants(updated_state)

        if self.counterfactual is not None and self.state.last_action:
            try:
                self.counterfactual.learn_from_outcome(
                    previous_state=previous_state,
                    inputs=clean_inputs,
                    actual_action=self.state.last_action,
                    actual_state=self.state.engine_state,
                    prior_goal=previous_goal,
                )
                self.state.last_regret = self.counterfactual.last_regret
                self.updater.record_regret(self.state.last_regret)
            except Exception:
                pass

        # Update somatic markers from the environment and previous action
        threat = max(clean_inputs.environmental_stress, clean_inputs.social_threat)
        action = self.state.last_action or ""
        safe = (threat < 0.25) and (clean_inputs.observed_state > 0.45)
        try:
            self.state.somatic.update(threat=threat, action=action, safe=safe)
        except Exception:
            pass

        # Appraise the event through the intrinsic value system and learn affective priors
        try:
            appraisal = self.state.value_system.evaluate_event(
                event=note or action,
                threat_level=threat,
                social_support=clean_inputs.social_support,
                uncertainty=clean_inputs.external_uncertainty,
            )
            label, intensity = self.state.value_system.appraise_from_threats(appraisal)
            self.state.value_system.update_from_outcome(
                event=note or action,
                emotion_label=label,
                intensity=intensity,
            )
            self.state.mood = clamp(self.state.mood + 0.05 * (0.5 - intensity), 0.0, 1.0)
        except Exception:
            pass

        # Propagate metacognition and allow somatic feedback to influence attitudes
        self.update_metacognition()
        self.update_plasticity(
            previous_state=previous_state,
            current_state=self.state.engine_state,
            inputs=clean_inputs,
            action=action,
        )

        if self.state.somatic.fatigue > 0.60:
            self.state.caution = clamp(self.state.caution + 0.12 * self.state.somatic.fatigue, 0.0, 1.0)
            self.state.confidence = clamp(self.state.confidence - 0.10 * self.state.somatic.fatigue, 0.0, 1.0)

        return self.state.engine_state

    def update_metacognition(self) -> None:
        frame = self.updater.memory_manager.narrative_frame(n_traces=12)
        narrative_coherence = frame.coherence if frame is not None else 0.5
        prediction_accuracy = self.peer_model.prediction_accuracy if self.peer_model is not None else self.state.engine_state.predictive_precision
        intuition_reliability = clamp(0.5 * (1.0 - self.state.engine_state.prediction_error) + 0.5 * self.state.engine_state.predictive_precision, 0.0, 1.0)

        self.state.recursive_self_model.update(prediction_accuracy, narrative_coherence, intuition_reliability)

        meta_accuracy = self.state.recursive_self_model.meta_accuracy
        identity_summary = self.updater.memory_manager.identity_summary()
        identity_coherence = identity_summary.coherence if identity_summary else 0.5

        self.state.confidence = clamp(
            self.state.confidence + 0.08 * (meta_accuracy - 0.5) + 0.05 * (identity_coherence - 0.5),
            0.0,
            1.0,
        )
        self.state.caution = clamp(
            self.state.caution + 0.12 * (0.5 - meta_accuracy) + 0.05 * (0.5 - identity_coherence),
            0.0,
            1.0,
        )

    def update_plasticity(
        self,
        previous_state: TheoryState,
        current_state: TheoryState,
        inputs: TheoryInputs,
        action: str,
    ) -> None:
        """Drift cognitive weights from lived outcomes."""
        style = self.state.adaptive_style
        capacity = (
            self.state.somatic.cognitive_capacity()
            if hasattr(self.state.somatic, "cognitive_capacity")
            else self.state.somatic.energy
        )
        overload = (
            current_state.prediction_error > 0.55
            and current_state.survival_loss > 0.65
            and (current_state.prediction_error + current_state.survival_loss) / 2.0 > capacity
        )
        if overload:
            style.overload_streak += 1
            style.trauma_load = clamp(style.trauma_load + 0.04 + 0.04 * (1.0 - capacity), 0.0, 1.0)
        else:
            style.overload_streak = max(0, style.overload_streak - 1)
            style.trauma_load = clamp(style.trauma_load - 0.004, 0.0, 1.0)

        if style.overload_streak >= 2:
            style.threat_sensitivity = clamp(style.threat_sensitivity + 0.025 * style.overload_streak, 0.75, 1.85)
            style.social_depth_bias = clamp(style.social_depth_bias - 0.015 * style.overload_streak, -0.35, 0.45)
            self.weights.w_social_from_threat = clamp(self.weights.w_social_from_threat + 0.010, 0.20, 0.80)
            self.weights.w_social_from_support = clamp(self.weights.w_social_from_support - 0.006, 0.20, 0.70)
            self.weights.w_consciousness_boundary = clamp(self.weights.w_consciousness_boundary + 0.004, 0.15, 0.40)

        clean_action = action.split()[0].lower() if action else ""
        survival_improved = previous_state.survival_loss - current_state.survival_loss
        prediction_improved = previous_state.prediction_error - current_state.prediction_error
        planned_success = (
            clean_action == "plan"
            and previous_state.survival_loss > 0.45
            and (survival_improved > 0.05 or prediction_improved > 0.08)
        )
        if planned_success:
            style.successful_plan_streak += 1
            style.plan_mastery = clamp(style.plan_mastery + 0.05, 0.0, 1.0)
            style.recursion_bias = clamp(style.recursion_bias + 0.020, -0.25, 0.60)
            style.self_model_bias = clamp(style.self_model_bias + 0.018, -0.20, 0.60)
            self.weights.w_recursion_self = clamp(self.weights.w_recursion_self + 0.010, 0.20, 0.65)
            self.weights.w_self_from_prediction = clamp(self.weights.w_self_from_prediction + 0.008, 0.10, 0.45)
            self.weights.w_self_from_consistency = clamp(self.weights.w_self_from_consistency + 0.006, 0.05, 0.35)
        else:
            style.successful_plan_streak = max(0, style.successful_plan_streak - 1)
            style.plan_mastery = clamp(style.plan_mastery - 0.003, 0.0, 1.0)

        self.updater.weights = self.weights
        if self.counterfactual is not None:
            self.counterfactual.weights = self.weights

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
            if s.trust_in_other > 0.50:
                recovery_boost = 0.12
            else:
                recovery_boost = 0.04
            s.trust_in_other = clamp(s.trust_in_other + recovery_boost, 0.0, 1.0)
            s.attachment = clamp(s.attachment + 0.05, 0.0, 1.0)
        if other_agent_action in {"withdraw", "cautious", "reject", "isolate"}:
            s.trust_in_other = clamp(s.trust_in_other * 0.75, 0.0, 1.0)
            s.caution = clamp(s.caution + 0.04, 0.0, 1.0)

        s.caution = clamp(s.caution + 0.05 * env_stress, 0.0, 1.0)
        s.confidence = clamp(s.confidence - 0.03 * env_stress + 0.02 * s.engine_state.consciousness_index, 0.0, 1.0)
        s.curiosity = clamp(s.curiosity + 0.01 * (1.0 - env_stress), 0.0, 1.0)

        # Somatic feedback into attitudes: fatigue and low energy increase caution
        try:
            s.caution = clamp(s.caution + 0.06 * s.somatic.fatigue, 0.0, 1.0)
            s.confidence = clamp(s.confidence - 0.05 * s.somatic.fatigue, 0.0, 1.0)
        except Exception:
            pass

    def update_peer_model(self, peer_action: str, peer_utterance: str, env_stress: float) -> None:
        if not hasattr(self, "peer_model") or self.peer_model is None:
            return

        self.peer_model.update_observation(peer_action, peer_utterance, env_stress)
        self.state.confidence = clamp(self.state.confidence + 0.05 * (self.peer_model.prediction_accuracy - 0.5), 0.0, 1.0)
        self.state.caution = clamp(self.state.caution + 0.08 * (0.5 - self.peer_model.prediction_accuracy), 0.0, 1.0)

    def plan_subgoals(self, primary_goal: str) -> List[str]:
        plans = {
            "stabilize_safety": ["shore_up_boundary", "reduce_threat", "conserve_energy"],
            "reduce_uncertainty": ["sample_environment", "update_model", "plan_action"],
            "build_support": ["signal_peers", "coordinate", "bond"],
            "reflect": ["pause", "reappraise", "model_self"],
            "recover_balance": ["slow_down", "repair", "rest"],
        }
        return plans.get(primary_goal, ["maintain_safety"])

    def evaluate_goal_candidates(self) -> List[tuple[str, float, float, str]]:
        state = self.state.engine_state
        inputs = self.last_inputs or TheoryInputs()
        style = self.state.adaptive_style
        candidates: List[tuple[str, float, float, str]] = []
        
        # Identity coherence modulates decision confidence
        # High coherence → more exploratory (boost uncertain goals)
        # Low coherence → more cautious (suppress uncertain goals)
        identity_coherence = 0.5  # Default neutral
        try:
            identity_summary = self.updater.memory_manager.identity_summary()
            identity_coherence = identity_summary.coherence if identity_summary else 0.5
        except Exception:
            pass
        
        # Identity coherence as decision confidence modifier
        # Range: 0.7 (low coherence) to 1.3 (high coherence)
        coherence_modifier = 0.7 + 0.6 * identity_coherence

        boundary_deficit = max(0.0, 0.75 - state.boundary_integrity)
        if boundary_deficit > 0.0 or state.survival_loss > 0.35:
            score = (
                boundary_deficit * 0.7 + state.survival_loss * 0.3
            ) * (1.0 + 0.25 * style.threat_sensitivity)
            opportunity = min(1.0, 1.0 - inputs.external_uncertainty)
            candidates.append(("stabilize_safety", score * (0.5 + opportunity * 0.5), opportunity, "I need to preserve my boundary and reduce immediate threat."))

        uncertainty_deficit = max(state.prediction_error, inputs.external_uncertainty)
        if uncertainty_deficit > 0.25:
            score = uncertainty_deficit * (1.0 + 0.20 * style.recursion_bias)
            # Identity coherence affects willingness to explore: high coherence = explore more
            score *= coherence_modifier
            opportunity = inputs.observed_state
            candidates.append(("reduce_uncertainty", score, opportunity, "I need better predictions before I commit to the next action."))

        social_deficit = max(0.0, 0.45 - inputs.social_support) * 0.6 + max(0.0, 0.45 - state.social_model_depth) * 0.4
        if social_deficit > 0.20:
            score = social_deficit * (1.0 + 0.20 * self.profile.support_sensitivity)
            # High identity coherence improves trust in social interactions
            score *= (0.8 + 0.4 * identity_coherence)
            opportunity = inputs.social_support
            candidates.append(("build_support", score, opportunity, "It is safer to build alliances and reduce isolation."))

        reflective_deficit = max(0.0, 0.5 - state.self_model_depth)
        if state.recursive_integration > 0.30 and reflective_deficit > 0.0:
            score = reflective_deficit * (1.0 + 0.20 * style.self_model_bias)
            opportunity = state.recursive_integration
            candidates.append(("reflect", score, opportunity, "I can use my self-model to make better choices."))

        recovery_deficit = max(0.0, 0.35 - state.affect_valence) + max(0.0, state.affect_arousal - 0.55)
        if recovery_deficit > 0.10:
            score = recovery_deficit
            opportunity = 1.0 - state.survival_loss
            candidates.append(("recover_balance", score, opportunity, "My internal state needs to stabilize before I proceed."))

        if not candidates:
            candidates.append(("maintain_safety", 0.05, 0.5, "I am maintaining a stable, low-risk posture."))

        return candidates

    def select_intention(self) -> None:
        candidates = self.evaluate_goal_candidates()
        primary, best_score, opportunity, rationale = max(candidates, key=lambda item: item[1])
        subgoals = self.plan_subgoals(primary)
        deficit = {"primary": max(0.0, 1.0 - min(1.0, best_score))}
        self.intentional_frame.reset(
            primary_goal=primary,
            subgoals=subgoals,
            urgency=min(1.0, best_score),
            alignment=min(1.0, 0.45 + opportunity * 0.55),
            opportunity=opportunity,
            rationale=rationale,
            value_deficits=deficit,
        )

    def _goal_is_satisfied(self) -> bool:
        state = self.state.engine_state
        current = self.intentional_frame.current_subgoal()
        if current == "shore_up_boundary":
            return state.boundary_integrity >= 0.75
        if current == "reduce_threat":
            return state.survival_loss <= 0.35
        if current == "conserve_energy":
            return state.thermodynamic_load <= 0.35
        if current == "sample_environment":
            return state.prediction_error <= 0.35
        if current == "update_model":
            return state.recursive_integration >= 0.40
        if current == "plan_action":
            return state.self_model_depth >= 0.50
        if current == "signal_peers":
            return state.social_model_depth >= 0.45
        if current == "coordinate":
            return (self.last_inputs.social_support >= 0.45) if self.last_inputs is not None else state.social_model_depth >= 0.45
        if current == "bond":
            return self.state.trust_in_other >= 0.45
        if current == "pause":
            return state.affect_arousal <= 0.55
        if current == "reappraise":
            return state.self_model_depth >= 0.45
        if current == "model_self":
            return state.self_model_depth >= 0.50
        if current == "slow_down":
            return state.affect_arousal <= 0.50
        if current == "repair":
            return state.affect_valence >= 0.25
        if current == "rest":
            return state.thermodynamic_load <= 0.30
        return False

    def _action_for_goal(self, task: str, state: TheoryState) -> str:
        mapping = {
            "shore_up_boundary": "defend",
            "reduce_threat": "withdraw" if state.survival_loss > 0.4 else "defend",
            "conserve_energy": "conserve",
            "sample_environment": "explore",
            "update_model": "plan",
            "plan_action": "reappraise",
            "signal_peers": "coordinate",
            "coordinate": "support",
            "bond": "bond",
            "pause": "wait",
            "reappraise": "reappraise",
            "model_self": "model_self",
            "slow_down": "conserve",
            "repair": "wait",
            "rest": "wait",
            "maintain_safety": "wait",
        }
        return mapping.get(task, "explore")

    def explain_goal_choice(self, action: str) -> str:
        current = self.intentional_frame.current_subgoal().replace("_", " ")
        return f"I choose {action} to achieve {current} because {self.intentional_frame.rationale}"

    def act(self) -> str:
        action = self.choose_action()
        explanation = self.explain_goal_choice(action)
        self.state.dialogue_history.append(explanation)
        self.state.dialogue_history = self.state.dialogue_history[-64:]
        return explanation

    def choose_action(self) -> str:
        meta_accuracy = self.state.recursive_self_model.meta_accuracy
        if not self.intentional_frame.is_active():
            self.select_intention()

        if self._goal_is_satisfied():
            self.intentional_frame.advance()

        if meta_accuracy > 0.70 and self.state.engine_state.survival_loss < 0.45:
            if self.intentional_frame.current_subgoal() == "maintain_safety":
                self.intentional_frame.subgoals = ["sample_environment", "update_model", "plan_action"]
                self.intentional_frame.urgency = max(self.intentional_frame.urgency, 0.55)

        # Metabolic-driven recovery: check reserves FIRST before other actions
        try:
            reserve_deficit = self.state.somatic.reservoir_deviation()
            cognitive_capacity = (
                self.state.somatic.cognitive_capacity()
                if hasattr(self.state.somatic, "cognitive_capacity")
                else self.state.somatic.energy
            )
            
            # Strong recovery drive when reserves are critically low
            if reserve_deficit > 0.55 or self.state.somatic.energy < 0.22 or cognitive_capacity < 0.25:
                self.intentional_frame.subgoals = ["rest", "repair", "recover_balance"]
                self.intentional_frame.active_subgoal_index = 0
                self.intentional_frame.urgency = 0.95
                self.intentional_frame.alignment = max(self.intentional_frame.alignment, 0.80)
                self.intentional_frame.rationale = (
                    "My reserves are critically depleted. Restoring metabolic capacity is the top priority."
                )
            # Mild recovery drive when reserves are depleted
            elif reserve_deficit > 0.35 or self.state.somatic.energy < 0.35 or cognitive_capacity < 0.35:
                if "rest" not in self.intentional_frame.subgoals and "recover_balance" not in self.intentional_frame.subgoals:
                    self.intentional_frame.subgoals = ["rest", "recover_balance"] + self.intentional_frame.subgoals[:1]
                    self.intentional_frame.active_subgoal_index = 0
                    self.intentional_frame.urgency = max(self.intentional_frame.urgency, 0.70)
        except Exception:
            pass

        # Energy-aware behavior: avoid overextending when energy is low or fatigue high
        try:
            cognitive_capacity = (
                self.state.somatic.cognitive_capacity()
                if hasattr(self.state.somatic, "cognitive_capacity")
                else self.state.somatic.energy
            )
            if self.state.somatic.energy < 0.25 or self.state.somatic.fatigue > 0.65 or cognitive_capacity < 0.28:
                if "rest" not in self.intentional_frame.subgoals:
                    self.intentional_frame.subgoals = ["rest", "repair"]
                    self.intentional_frame.active_subgoal_index = 0
                    self.intentional_frame.urgency = max(self.intentional_frame.urgency, 0.60)
        except Exception:
            pass

        if self.peer_model is not None:
            predicted_peer_action = self.peer_model.predicted_action
            current_task = self.intentional_frame.current_subgoal()
            if current_task in {"signal_peers", "coordinate", "bond"}:
                if predicted_peer_action in {"bond", "support", "coordinate"}:
                    self.intentional_frame.subgoals = ["bond", "coordinate"]
                elif predicted_peer_action in {"defend", "withdraw"}:
                    self.intentional_frame.subgoals = ["coordinate", "signal_peers"]
            if predicted_peer_action == "withdraw" and self.state.trust_in_other < 0.40:
                self.intentional_frame.subgoals = ["reduce_threat", "conserve_energy"]

        if self.state.value_system is not None and self.last_inputs is not None:
            goal_scores = self.state.value_system.score_goals(
                goals=self.intentional_frame.subgoals,
                threat=self.state.engine_state.survival_loss,
                social_support=self.last_inputs.social_support,
                uncertainty=self.last_inputs.external_uncertainty,
            )
            # pick best goal robustly from (goal, score) pairs
            if goal_scores:
                best_goal = max(goal_scores.items(), key=lambda kv: kv[1])[0]
                current_goal = self.intentional_frame.current_subgoal()
                if goal_scores.get(best_goal, 0.0) - goal_scores.get(current_goal, 0.0) > 0.12:
                    try:
                        self.intentional_frame.active_subgoal_index = self.intentional_frame.subgoals.index(best_goal)
                    except ValueError:
                        pass
            self.intentional_frame.value_deficits = {
                key: clamp(1.0 - value, 0.0, 1.0)
                for key, value in self.state.value_system.satisfaction.items()
            }

        try:
            cognitive_capacity = (
                self.state.somatic.cognitive_capacity()
                if hasattr(self.state.somatic, "cognitive_capacity")
                else self.state.somatic.energy
            )
            if self.state.somatic.energy < 0.18 or self.state.somatic.fatigue > 0.80 or cognitive_capacity < 0.20:
                self.intentional_frame.subgoals = ["rest", "repair"]
                self.intentional_frame.active_subgoal_index = 0
                self.intentional_frame.urgency = 0.90
                self.intentional_frame.alignment = max(self.intentional_frame.alignment, 0.75)
                self.intentional_frame.rationale = (
                    "My body is near depletion, so restoring metabolic capacity must come before further defense."
                )
        except Exception:
            pass

        if self.counterfactual is not None:
            candidate = self.counterfactual.propose_action(
                current_goal=self.intentional_frame.current_subgoal(),
                current_state=self.state.engine_state,
                current_inputs=self.last_inputs,
            )
        else:
            candidate = SimpleNamespace(
                action=self._action_for_goal(self.intentional_frame.current_subgoal(), self.state.engine_state),
                narrative=self.intentional_frame.rationale,
            )

        action = candidate.action
        self.intentional_frame.rationale = candidate.narrative
        self.intentional_frame.persistence += 1
        if self.intentional_frame.persistence >= self.intentional_frame.max_persistence:
            self.intentional_frame.achieved = True

        # Consume somatic energy for the chosen action and record it
        try:
            self.state.somatic.consume_energy(action)
        except Exception:
            pass

        self.state.last_action = action
        return action

    def generate_report(self) -> str:
        s = self.state.engine_state
        # OPERATOR FIX: Query memory through the updater
        idn = self.updater.memory_manager.identity_summary()
        report = (
            f"{self.name}: loss={s.survival_loss:.3f}, boundary={s.boundary_integrity:.3f}, "
            f"self={s.self_model_depth:.3f}, social={s.social_model_depth:.3f}, "
            f"recursion={s.recursive_integration:.3f}, conc={s.consciousness_index:.3f}, "
            f"identity={idn.identity_stability:.3f}"
        )
        self.state.last_report = report
        return report

    def speak(self, peer_utterance: str = "") -> str:
        s = self.state.engine_state
        action = self.state.last_action or "wait"
        emotions = self.get_emotions()
        rationale = self.intentional_frame.rationale

        recent_memory = None
        try:
            frame = self.updater.memory_manager.narrative_frame(n_traces=10)
            recent_memory = frame.sentences if frame is not None else None
        except Exception:
            recent_memory = None

        # Build a typed emotional_state mapping for the language generator using engine values
        emotional_state = {
            "affect_valence": float(s.affect_valence),
            "affect_arousal": float(s.affect_arousal),
            "confidence": float(self.state.confidence),
            "caution": float(self.state.caution),
            "trust_in_other": float(self.state.trust_in_other),
            "self_model_depth": float(s.self_model_depth),
            "social_model_depth": float(s.social_model_depth),
        }

        primary_emotion = str(emotions.get("primary_emotion", "neutral"))
        somatic_state = self.state.somatic.as_dict() if hasattr(self.state, "somatic") else None

        msg = self.language_generator.generate(
            emotional_state=emotional_state,
            somatic_state=somatic_state,
            primary_emotion=primary_emotion,
            intended_action=action,
            action_rationale=rationale,
            goal=self.intentional_frame.primary_goal,
            dialogue_history=self.state.dialogue_history,
            peer_utterance=peer_utterance,
            recent_memory=recent_memory,
        )

        self.state.dialogue_history.append(msg)
        self.state.dialogue_history = self.state.dialogue_history[-64:]
        return msg

    def get_emotions(self) -> Dict[str, object]:
        """Classify current emotional context from affect, social, and self-model state."""
        eng = self.state.engine_state
        s = self.state
        labels: List[str] = []
        valence = eng.affect_valence
        arousal = eng.affect_arousal
        threat = eng.survival_loss
        pred_error = eng.prediction_error
        trust_other = s.trust_in_other
        confidence = s.confidence
        self_depth = eng.self_model_depth
        social_depth = eng.social_model_depth

        if valence >= 0.65 and arousal <= 0.45:
            labels.append("content")
        if valence >= 0.65 and arousal > 0.45:
            labels.append("enthusiastic")
        if 0.45 <= valence < 0.65 and arousal > 0.55:
            labels.append("curious")
        if valence < 0.45 and arousal > 0.60:
            if social_depth > 0.50 and trust_other < 0.45:
                labels.append("embarrassed")
            elif pred_error > 0.55:
                labels.append("anxious")
            elif threat > 0.55:
                labels.append("afraid")
            else:
                labels.append("distressed")
        if valence < 0.45 and arousal <= 0.60:
            if social_depth > 0.50 and trust_other < 0.40:
                labels.append("alienated")
            else:
                labels.append("sad")
        if valence > 0.55 and trust_other > 0.60 and social_depth > 0.55:
            labels.append("affiliative")
        if valence > 0.50 and arousal > 0.60 and self_depth > 0.50:
            labels.append("motivated")
        if pred_error > 0.60 and arousal > 0.45:
            labels.append("surprised")
        if not labels:
            if arousal > 0.60:
                labels.append("alert")
            else:
                labels.append("neutral")

        # Integrate somatic classification
        try:
            som_label = classify_somatic_emotion(self.state.somatic, valence)
            if som_label not in labels:
                labels.insert(0, som_label)
        except Exception:
            som_label = "unknown"

        return {
            "emotion_labels": labels,
            "primary_emotion": labels[0] if labels else "neutral",
            "affect_valence": valence,
            "affect_arousal": arousal,
            "trust_in_other": trust_other,
            "confidence": confidence,
            "self_model_depth": self_depth,
            "social_model_depth": social_depth,
            "somatic": self.state.somatic.as_dict() if hasattr(self.state, "somatic") else {},
        }

    def get_layer_state(self, layer_name: str) -> Dict[str, object]:
        """Return a small state dictionary for a named theory layer."""
        clean = layer_name.strip().lower()
        eng = self.state.engine_state
        if clean in {"survival", "survival_loss"}:
            return {
                "viability": eng.viability,
                "boundary_integrity": eng.boundary_integrity,
                "thermodynamic_load": eng.thermodynamic_load,
                "survival_loss": eng.survival_loss,
            }
        if clean in {"prediction", "prediction_error"}:
            return {
                "prediction_error": eng.prediction_error,
                "predictive_precision": eng.predictive_precision,
            }
        if clean in {"affect", "emotion", "affect_valence"}:
            return {
                "affect_valence": eng.affect_valence,
                "affect_arousal": eng.affect_arousal,
            }
        if clean in {"self", "self_model", "self_model_depth"}:
            return {
                "self_model_depth": eng.self_model_depth,
                "self_consistency": self.state.confidence,
            }
        if clean in {"social", "social_model_depth"}:
            return {
                "social_model_depth": eng.social_model_depth,
                "trust_in_other": self.state.trust_in_other,
                "attachment": self.state.attachment,
            }
        if clean in {"recursion", "recursive", "recursive_integration"}:
            return {
                "recursive_integration": eng.recursive_integration,
                "curiosity": self.state.curiosity,
            }
        if clean in {"language", "language_stability"}:
            return {
                "language_stability": eng.language_stability,
                "language_support_bias": self.profile.language_bias,
            }
        if clean in {"plasticity", "adaptive_style", "personality"}:
            return self.state.adaptive_style.as_dict()
        if clean in {"subjective", "subjective_experience"}:
            return {
                "subjective_experience": eng.subjective_experience,
                "consciousness_index": eng.consciousness_index,
            }
        if clean in {"consciousness", "consciousness_index"}:
            return {
                "consciousness_index": eng.consciousness_index,
                "global_integration": eng.global_integration,
            }
        if clean in {"emotion", "emotions"}:
            emotion_data = self.get_emotions()
            labels = cast(Sequence[str], emotion_data.get("emotion_labels", []))
            return {
                "primary_emotion": emotion_data["primary_emotion"],
                "emotion_labels": ", ".join(labels),
                "affect_valence": emotion_data["affect_valence"],
                "affect_arousal": emotion_data["affect_arousal"],
                "trust_in_other": emotion_data["trust_in_other"],
                "confidence": emotion_data["confidence"],
            }
        if clean in {"memory", "memories"}:
            bank = self.updater.memory_manager.bank
            return {
                "memory_depth": len(bank.traces),
                "salient_count": len(bank.salient_traces),
            }
        if clean in {"trust", "trust_in_user", "trust_in_other"}:
            return {
                "trust_in_user": self.state.trust_in_user,
                "trust_in_other": self.state.trust_in_other,
            }
        if clean == "mood":
            return {"mood": self.state.mood, "confidence": self.state.confidence}
        raise KeyError(f"No layer state available for '{layer_name}'")

    def snapshot(self) -> Dict[str, Any]:
        s = self.state
        eng = s.engine_state
        base_snap: Dict[str, Any] = {
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
            "value_system_score": self.state.value_system.overall_score(),
            "plastic_threat_sensitivity": s.adaptive_style.threat_sensitivity,
            "plastic_social_depth_bias": s.adaptive_style.social_depth_bias,
            "plastic_recursion_bias": s.adaptive_style.recursion_bias,
            "plastic_self_model_bias": s.adaptive_style.self_model_bias,
            "trauma_load": s.adaptive_style.trauma_load,
            "plan_mastery": s.adaptive_style.plan_mastery,
        }
        if hasattr(self, "peer_model") and self.peer_model is not None:
            base_snap["peer_model_accuracy"] = self.peer_model.prediction_accuracy
            base_snap["peer_predicted_action"] = float(hash(self.peer_model.predicted_action) % 1000)
            base_snap["peer_estimated_alignment"] = self.peer_model.estimated_alignment
            base_snap["peer_estimated_trust"] = self.peer_model.estimated_trust
        else:
            base_snap.update({
                "peer_model_accuracy": 0.0,
                "peer_predicted_action": 0.0,
                "peer_estimated_alignment": 0.0,
                "peer_estimated_trust": 0.0,
            })
        emotion_data = self.get_emotions()
        labels = cast(Sequence[str], emotion_data.get("emotion_labels", []))
        base_snap["emotion_labels"] = ", ".join(labels)
        base_snap["primary_emotion"] = emotion_data["primary_emotion"]
        return base_snap

    def recent_memories(self, n: int = 5) -> List[MemoryTrace]:
        # OPERATOR FIX: Query memory through the updater
        return self.updater.memory_manager.recent_traces(n)

    def reset(self) -> None:
        self.state = AgentState(name=self.name, profile=self.profile)
        self.weights = deepcopy(self.base_weights)
        self.updater.reset()
        self.updater.weights = self.weights
        self.counterfactual.weights = self.weights


def make_agent(name: str, profile_name: str = "hybrid", seed: Optional[int] = None) -> AgentEngine:
    return AgentEngine(name=name, profile_name=profile_name, seed=seed)


def make_pair(seed: Optional[int] = None) -> Tuple[AgentEngine, AgentEngine]:
    a = AgentEngine(name="A", profile_name="active_inf", seed=seed)
    b = AgentEngine(name="B", profile_name="recursive", seed=None if seed is None else seed + 1)
    a.peer_model = PeerCognitiveModel(target_name="B")
    b.peer_model = PeerCognitiveModel(target_name="A")
    return a, b
