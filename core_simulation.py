#!/usr/bin/env python3
"""
core_simulation.py

Upgraded simulation orchestrator for the Evolutionary Survival Theory of Consciousness.
Establishes symmetric, closed-loop multi-agent active inference coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple
import random

from core_types import TheoryConfig, TheoryInputs, TheoryState, TheoryWeights
from core_environment import EnvironmentEngine, EnvironmentMode, EnvironmentEvent, get_event
from core_agents import AgentEngine, make_pair
from core_ablation import AblationConfig, AblationPreset, PRESETS, active_layers_from_config
from core_metrics import MetricSummary, summarize_state, summarize_traces, rank_layers
from core_memory import MemoryTrace, IdentitySummary


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass(frozen=True)
class StepRecord:
    step_index: int
    environment: Dict[str, float]
    agent_a: Dict[str, float]
    agent_b: Dict[str, float]
    user_action: str = ""
    mode: str = ""
    event: str = ""


@dataclass
class SimulationResult:
    records: List[StepRecord] = field(default_factory=list)
    final_summary_a: Optional[MetricSummary] = None
    final_summary_b: Optional[MetricSummary] = None
    final_identity_a: Optional[IdentitySummary] = None
    final_identity_b: Optional[IdentitySummary] = None


class TheorySimulation:
    """Runs the theory engine as an integrated coupled system with recursive feedback."""

    def __init__(
        self,
        agent_a: Optional[AgentEngine] = None,
        agent_b: Optional[AgentEngine] = None,
        environment: Optional[EnvironmentEngine] = None,
        ablation: Optional[AblationConfig] = None,
        seed: Optional[int] = None,
    ):
        self.rng = random.Random(seed)
        self.environment = environment or EnvironmentEngine(seed=seed)
        self.agent_a = agent_a or make_pair(seed=seed)[0]
        self.agent_b = agent_b or make_pair(seed=seed)[1]
        self.ablation = ablation or AblationConfig()
        self.history: List[StepRecord] = []
        
        # Seed default historical states to anchor the initial step loop
        if not getattr(self.agent_a.state, "last_action", None):
            self.agent_a.state.last_action = "wait"
        if not getattr(self.agent_b.state, "last_action", None):
            self.agent_b.state.last_action = "wait"

    def step(
        self,
        mode: Optional[EnvironmentMode] = None,
        event: Optional[EnvironmentEvent] = None,
        user_action_a: str = "",
        user_action_b: str = "",
        observed_state_a: Optional[float] = None,
        observed_state_b: Optional[float] = None,
        prediction_target_a: Optional[float] = None,
        prediction_target_b: Optional[float] = None,
        language_support_a: float = 0.0,
        language_support_b: float = 0.0,
    ) -> StepRecord:
        
        # 1) Advance the environment state parameters
        env_state = self.environment.step(mode=mode, event=event)
        env_snapshot = self.environment.snapshot()
        live_volatility = env_snapshot.get("volatility", 0.5)
        
        # Safe string conversion for Enum objects to prevent downstream type crashes
        current_mode = env_state.mode.name.lower() if hasattr(env_state.mode, 'name') else str(env_state.mode).lower()

        # 2) AUTOMATIC CLOSED-LOOP FALLBACKS & BEHAVIORAL HEURISTICS
        clean_a = user_action_a.split()[0].lower() if user_action_a else ""

        if not user_action_b and current_mode in {"social", "stress", "crisis"}:
            if clean_a in {"isolate", "threaten", "reject"}:
                user_action_b = "support"
            elif current_mode == "social":
                user_action_b = "coordinate"
            else:
                user_action_b = "wait"

        if not user_action_a and (current_mode == "crisis" or (event and event.name == "alarm")):
            user_action_a = "defend"

        if observed_state_a is None:
            observed_state_a = live_volatility
        if observed_state_b is None:
            observed_state_b = live_volatility

        if prediction_target_a is None:
            prediction_target_a = clamp(0.2 + 0.3 * self.agent_a.state.caution, 0.0, 1.0)
        if prediction_target_b is None:
            prediction_target_b = clamp(0.2 + 0.3 * self.agent_b.state.caution, 0.0, 1.0)

        # 3) Build execution matrices
        # DECOUPLE THE OPERATOR FROM THE AGENT
        # The agent acts physically via its own last_action; the Operator acts via user_action
        agent_a_act = self.agent_a.state.last_action
        agent_b_act = self.agent_b.state.last_action

        # Combine incoming environmental signals (From the peer agent + the primary operator)
        social_signal_multiplier = 1.2 if current_mode == "crisis" else 1.0
        incoming_signal_a = clamp(_social_signal(agent_b_act) + _social_signal(user_action_a), 0.0, 1.0)
        incoming_signal_b = clamp(_social_signal(agent_a_act) + _social_signal(user_action_b), 0.0, 1.0)

        inputs_a = self.agent_a.build_inputs(
            environment=self.environment,
            observed_state=observed_state_a,
            prediction_target=prediction_target_a,
            action_cost=_action_cost(agent_a_act),  # Agent pays for its OWN autonomous choices
            social_signal=incoming_signal_a * social_signal_multiplier,
            language_support=language_support_a,
        )
        inputs_b = self.agent_b.build_inputs(
            environment=self.environment,
            observed_state=observed_state_b,
            prediction_target=prediction_target_b,
            action_cost=_action_cost(agent_b_act),  # Agent pays for its OWN autonomous choices
            social_signal=incoming_signal_b * social_signal_multiplier,
            language_support=language_support_b,
        )

        # 4) Process mathematical updates through layers
        self.agent_a.perceive_and_update(inputs_a, note=agent_a_act or str(mode) or current_mode)
        self.agent_b.perceive_and_update(inputs_b, note=agent_b_act or str(mode) or current_mode)

        # 5) Track attitudes (Agent independently tracks Operator behavior vs Peer behavior)
        self.agent_a.update_attitudes(user_action_a, agent_b_act, env_state.stress)
        self.agent_b.update_attitudes(user_action_b, agent_a_act, env_state.stress)

        # 6) Action mapping lookup (ALLOW AGENTS TRUE AUTONOMY)
        action_a = self.agent_a.choose_action()
        action_b = self.agent_b.choose_action()

        self.agent_a.state.last_action = action_a
        self.agent_b.state.last_action = action_b

        # 7) Clean Output Serialization (Dead code completely purged)
        rec = StepRecord(
            step_index=env_state.step_index,
            environment=self.environment.snapshot(),
            agent_a={**self.agent_a.snapshot(), "chosen_action": action_a.upper()},
            agent_b={**self.agent_b.snapshot(), "chosen_action": action_b.upper()},
            user_action=f"A:{user_action_a} | B:{user_action_b}",
            mode=current_mode,
            event=event.name if event is not None else "",
        )

        self.history.append(rec)
        return rec

    def run(self, steps: int, script: Optional[Sequence[Dict[str, object]]] = None) -> SimulationResult:
        script = list(script or [])
        result = SimulationResult()

        for i in range(steps):
            frame = script[i] if i < len(script) else {}
            mode = frame.get("mode")
            event_name = frame.get("event")
            event = get_event(str(event_name)) if event_name else None

            ob_a = frame.get("observed_state_a")
            ob_b = frame.get("observed_state_b")
            pt_a = frame.get("prediction_target_a")
            pt_b = frame.get("prediction_target_b")

            rec = self.step(
                mode=mode if isinstance(mode, str) else None,
                event=event,
                user_action_a=str(frame.get("user_action_a", "")),
                user_action_b=str(frame.get("user_action_b", "")),
                observed_state_a=float(ob_a) if ob_a is not None else None,
                observed_state_b=float(ob_b) if ob_b is not None else None,
                prediction_target_a=float(pt_a) if pt_a is not None else None,
                prediction_target_b=float(pt_b) if pt_b is not None else None,
                language_support_a=float(frame.get("language_support_a", 0.0)),
                language_support_b=float(frame.get("language_support_b", 0.0)),
            )
            result.records.append(rec)

        result.final_summary_a = summarize_state(self.agent_a.state.engine_state, self.agent_a.state.memory.identity_summary())
        result.final_summary_b = summarize_state(self.agent_b.state.engine_state, self.agent_b.state.memory.identity_summary())
        result.final_identity_a = self.agent_a.state.memory.identity_summary()
        result.final_identity_b = self.agent_b.state.memory.identity_summary()
        return result

    def summarize(self) -> Dict[str, Dict[str, float]]:
        env = self.environment.snapshot()
        id_a = self.agent_a.state.memory.identity_summary()
        id_b = self.agent_b.state.memory.identity_summary()
        return {
            "environment": env,
            "agent_a": summarize_state(self.agent_a.state.engine_state, id_a).as_dict(),
            "agent_b": summarize_state(self.agent_b.state.engine_state, id_b).as_dict(),
        }

    def traces(self) -> Dict[str, List[MemoryTrace]]:
        return {
            "agent_a": self.agent_a.recent_memories(64),
            "agent_b": self.agent_b.recent_memories(64),
        }

    def layer_ranking(self, agent: str = "a") -> List[Tuple[str, float]]:
        if agent.lower() in {"a", "agent_a"}:
            return rank_layers(self.agent_a.state.engine_state, self.agent_a.state.memory.identity_summary())
        return rank_layers(self.agent_b.state.engine_state, self.agent_b.state.memory.identity_summary())

    def reset(self) -> None:
        self.history = []
        self.environment = EnvironmentEngine(seed=self.rng.randint(0, 10**9))
        self.agent_a.reset()
        self.agent_b.reset()
        self.agent_a.state.last_action = "wait"
        self.agent_b.state.last_action = "wait"


class AblationSimulation(TheorySimulation):
    def __init__(
        self,
        preset_name: str = "full_theory",
        agent_a: Optional[AgentEngine] = None,
        agent_b: Optional[AgentEngine] = None,
        environment: Optional[EnvironmentEngine] = None,
        seed: Optional[int] = None,
    ):
        if preset_name not in PRESETS:
            raise KeyError(f"Unknown ablation preset: {preset_name}")
        self.preset = PRESETS[preset_name]
        super().__init__(agent_a=agent_a, agent_b=agent_b, environment=environment, ablation=self.preset.config, seed=seed)

    def summary(self) -> Dict[str, object]:
        base = self.summarize()
        base["ablation"] = {
            "preset": self.preset.name,
            "disabled_layers": self.preset.config.disabled_layers,
            "active_layers": active_layers_from_config(self.preset.config),
            "description": self.preset.description,
        }
        return base


def _action_cost(action: str) -> float:
    if not action:
        return 0.0
    clean_token = action.split()[0].lower() if isinstance(action, str) else ""
    cost_map = {
        "wait": 0.02, "observe": 0.02, "explore": 0.08, "plan": 0.10, "reappraise": 0.06,
        "model_self": 0.08, "signal": 0.04, "coordinate": 0.06, "bond": 0.05, "support": 0.06,
        "negotiate": 0.07, "seek": 0.05, "seek_alliance": 0.08, "conserve": 0.03,
        "withdraw": 0.02, "defend": 0.07, "hide": 0.05, "reflect": 0.05
    }
    return cost_map.get(clean_token, 0.05)


def _social_signal(action: str) -> float:
    if not action:
        return 0.0
    clean_token = action.split()[0].lower() if isinstance(action, str) else ""
    if clean_token in {"help", "feed", "bond", "support", "seek_alliance", "negotiate", "coordinate"}:
        return 0.10
    if clean_token in {"threaten", "isolate", "reject", "withdraw", "defend", "hide"}:
        return 0.08
    return 0.0


def _hash_action(action: str) -> float:
    if not action:
        return 0.0
    return float(abs(hash(action)) % 1000) / 1000.0


def make_simulation(seed: Optional[int] = None) -> TheorySimulation:
    return TheorySimulation(seed=seed)


def make_ablation_simulation(preset_name: str = "full_theory", seed: Optional[int] = None) -> AblationSimulation:
    return AblationSimulation(preset_name=preset_name, seed=seed)