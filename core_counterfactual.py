#!/usr/bin/env python3
"""
core_counterfactual.py

Counterfactual reasoning module for the Evolutionary Survival Theory of Consciousness.
This module imagines alternate actions, predicts future outcomes, computes regret,
and updates action preference weights so agents learn from "what if" scenarios.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import List, Optional

from core_types import TheoryConfig, TheoryInputs, TheoryState, TheoryWeights
from core_update import TheoryUpdater


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass
class CounterfactualOutcome:
    action: str
    predicted_state: TheoryState
    predicted_score: float
    pragmatic_value: float = 0.0
    epistemic_value: float = 0.0
    gamma: float = 1.0
    expected_free_energy: float = 0.0
    regret: float = 0.0
    narrative: str = ""


class CounterfactualSimulator:
    """Simulates alternate actions and selects policies by expected free energy."""

    def __init__(
        self,
        weights: Optional[TheoryWeights] = None,
        config: Optional[TheoryConfig] = None,
    ):
        self.weights = weights or TheoryWeights()
        self.config = config or TheoryConfig()
        self.regret_history: List[float] = []
        self.last_regret: float = 0.0

    def _clone_updater(self, state: TheoryState) -> TheoryUpdater:
        return TheoryUpdater(
            weights=self.weights,
            config=self.config,
            initial_state=deepcopy(state),
        )

    def _goal_candidates(self, goal: str) -> List[str]:
        mapping = {
            "shore_up_boundary": ["defend", "withdraw", "wait"],
            "reduce_threat": ["withdraw", "defend", "hide"],
            "conserve_energy": ["conserve", "rest", "wait"],
            "sample_environment": ["explore", "plan", "wait"],
            "update_model": ["plan", "reappraise", "model_self"],
            "plan_action": ["reappraise", "plan", "explore"],
            "signal_peers": ["coordinate", "bond", "support"],
            "coordinate": ["support", "bond", "explore"],
            "bond": ["bond", "support", "wait"],
            "pause": ["wait", "conserve", "rest"],
            "reappraise": ["plan", "model_self", "wait"],
            "model_self": ["model_self", "reappraise", "wait"],
            "slow_down": ["conserve", "rest", "wait"],
            "repair": ["rest", "wait", "conserve"],
            "rest": ["rest", "wait", "conserve"],
            "maintain_safety": ["wait", "defend", "conserve"],
        }
        return mapping.get(goal, ["wait", "explore", "plan"])

    def _action_adjusted_inputs(self, inputs: TheoryInputs, action: str) -> TheoryInputs:
        threat = inputs.social_threat
        stress = inputs.environmental_stress
        support = inputs.social_support
        observed = inputs.observed_state
        action_cost = inputs.action_cost
        uncertainty = inputs.external_uncertainty
        metabolic_reserve = inputs.metabolic_reserve
        hydration = inputs.hydration
        oxygenation = inputs.oxygenation
        immune_load = inputs.immune_load
        neural_energy = inputs.neural_energy

        if action == "defend":
            threat *= 0.40
            stress *= 0.60
            metabolic_reserve = clamp(metabolic_reserve - 0.025, 0.0, 1.0)
            oxygenation = clamp(oxygenation - 0.030, 0.0, 1.0)
        elif action == "withdraw":
            threat *= 0.70
            stress *= 0.30
            metabolic_reserve = clamp(metabolic_reserve - 0.020, 0.0, 1.0)
            oxygenation = clamp(oxygenation - 0.020, 0.0, 1.0)
        elif action == "hide":
            threat *= 0.10
            stress *= 0.80
            metabolic_reserve = clamp(metabolic_reserve - 0.015, 0.0, 1.0)
        elif action in {"bond", "support", "coordinate"}:
            support = clamp(support + 0.18, 0.0, 1.0)
            threat = clamp(threat - 0.15, 0.0, 1.0)
            uncertainty = clamp(uncertainty - 0.04, 0.0, 1.0)
            metabolic_reserve = clamp(metabolic_reserve - 0.015, 0.0, 1.0)
            neural_energy = clamp(neural_energy - 0.020, 0.0, 1.0)
        elif action == "plan":
            observed = clamp(observed + 0.08, 0.0, 1.0)
            action_cost = clamp(action_cost + 0.015, 0.0, 1.0)
            uncertainty = clamp(uncertainty - 0.08, 0.0, 1.0)
            neural_energy = clamp(neural_energy - 0.050, 0.0, 1.0)
            metabolic_reserve = clamp(metabolic_reserve - 0.012, 0.0, 1.0)
        elif action == "explore":
            observed = clamp(observed + 0.10, 0.0, 1.0)
            support = clamp(support + 0.05, 0.0, 1.0)
            uncertainty = clamp(uncertainty - 0.14, 0.0, 1.0)
            metabolic_reserve = clamp(metabolic_reserve - 0.030, 0.0, 1.0)
            hydration = clamp(hydration - 0.030, 0.0, 1.0)
            neural_energy = clamp(neural_energy - 0.035, 0.0, 1.0)
        elif action in {"conserve", "rest"}:
            action_cost = clamp(action_cost - 0.12, 0.0, 1.0)
            stress = clamp(stress - 0.08, 0.0, 1.0)
            observed = clamp(observed + 0.05, 0.0, 1.0)
            uncertainty = clamp(uncertainty - 0.02, 0.0, 1.0)
            metabolic_reserve = clamp(metabolic_reserve + 0.035, 0.0, 1.0)
            neural_energy = clamp(neural_energy + 0.030, 0.0, 1.0)
            immune_load = clamp(immune_load - 0.010, 0.0, 1.0)
        elif action in {"reappraise", "model_self"}:
            observed = clamp(observed + 0.08, 0.0, 1.0)
            action_cost = clamp(action_cost + 0.01, 0.0, 1.0)
            stress = clamp(stress - 0.03, 0.0, 1.0)
            uncertainty = clamp(uncertainty - 0.06, 0.0, 1.0)
            neural_energy = clamp(neural_energy - 0.035, 0.0, 1.0)
            metabolic_reserve = clamp(metabolic_reserve - 0.006, 0.0, 1.0)

        return TheoryInputs(
            homeostatic_deviation=inputs.homeostatic_deviation,
            environmental_stress=stress,
            prediction_target=inputs.prediction_target,
            observed_state=observed,
            social_threat=threat,
            social_support=support,
            language_support=inputs.language_support,
            action_cost=action_cost,
            metabolic_reserve=metabolic_reserve,
            hydration=hydration,
            oxygenation=oxygenation,
            immune_load=immune_load,
            neural_energy=neural_energy,
            memory_depth=inputs.memory_depth,
            self_consistency=inputs.self_consistency,
            external_uncertainty=uncertainty,
            peer_prediction_accuracy=inputs.peer_prediction_accuracy,
            goal_urgency=inputs.goal_urgency,
            goal_alignment=inputs.goal_alignment,
            meta_accuracy=inputs.meta_accuracy,
        )

    def evaluate_state(self, state: TheoryState) -> float:
        metabolic_penalty = clamp(0.30 * (1.0 - state.thermodynamic_load), 0.0, 0.30)
        score = (
            0.22 * (1.0 - state.survival_loss)
            + 0.18 * (1.0 - state.prediction_error)
            + 0.15 * state.self_model_depth
            + 0.15 * state.social_model_depth
            + 0.15 * state.subjective_experience
            + 0.15 * state.consciousness_index
            - metabolic_penalty
        )
        return clamp(score, 0.0, 1.0)

    def _describe_state(self, state: TheoryState) -> str:
        if state.self_model_depth > 0.65 and state.social_model_depth > 0.55:
            return "more self-aware and socially attuned"
        if state.self_model_depth > 0.65:
            return "more self-aware and deliberate"
        if state.social_model_depth > 0.55:
            return "more connected and cooperative"
        if state.survival_loss < 0.30:
            return "safer and more resilient"
        if state.prediction_error < 0.35:
            return "more confident in my predictions"
        return "more balanced"

    def epistemic_gamma(self, inputs: TheoryInputs) -> float:
        """
        Dynamic precision weight for epistemic value.

        In the live simulation observed_state is normally fed from environmental volatility,
        so volatile/uncertain contexts raise the value of information-seeking policies.
        """
        volatility_proxy = inputs.observed_state
        return clamp(0.25 + 1.25 * volatility_proxy + 0.50 * inputs.external_uncertainty, 0.25, 2.0)

    def expected_free_energy(
        self,
        current_state: TheoryState,
        predicted_state: TheoryState,
        current_inputs: TheoryInputs,
        imagined_inputs: TheoryInputs,
    ) -> tuple[float, float, float, float]:
        """
        Formal active-inference policy value:

            G(a) = -(PragmaticValue(a) + gamma * EpistemicValue(a))

        The negative sign lets action selection minimize expected free energy while the
        component values remain intuitive positive reductions.
        """
        # Include metabolic cost penalty for predicted thermodynamic load
        pragmatic_value = clamp(
            current_state.survival_loss
            - predicted_state.survival_loss
            - clamp(0.30 * (1.0 - predicted_state.thermodynamic_load), 0.0, 0.30),
            -1.0,
            1.0,
        )
        uncertainty_reduction = current_inputs.external_uncertainty - imagined_inputs.external_uncertainty
        prediction_error_reduction = current_state.prediction_error - predicted_state.prediction_error
        epistemic_value = clamp(
            0.60 * uncertainty_reduction + 0.40 * prediction_error_reduction,
            -1.0,
            1.0,
        )
        gamma = self.epistemic_gamma(current_inputs)
        efe = -(pragmatic_value + gamma * epistemic_value)
        return efe, pragmatic_value, epistemic_value, gamma

    def build_prospective_narrative(self, outcome: CounterfactualOutcome) -> str:
        future_description = self._describe_state(outcome.predicted_state)
        return (
            f"If I do {outcome.action}, I will become {future_description}"
            f" with pragmatic value {outcome.pragmatic_value:.2f}, epistemic value {outcome.epistemic_value:.2f}, "
            f"gamma {outcome.gamma:.2f}, and expected free energy {outcome.expected_free_energy:.2f}."
        )

    def simulate_action(self, state: TheoryState, inputs: TheoryInputs, action: str) -> CounterfactualOutcome:
        updater = self._clone_updater(state)
        imagined_inputs = self._action_adjusted_inputs(inputs, action)
        predicted_state = updater.step(imagined_inputs)
        predicted_score = self.evaluate_state(predicted_state)
        efe, pragmatic_value, epistemic_value, gamma = self.expected_free_energy(
            current_state=state,
            predicted_state=predicted_state,
            current_inputs=inputs,
            imagined_inputs=imagined_inputs,
        )
        outcome = CounterfactualOutcome(
            action=action,
            predicted_state=predicted_state,
            predicted_score=predicted_score,
            pragmatic_value=pragmatic_value,
            epistemic_value=epistemic_value,
            gamma=gamma,
            expected_free_energy=efe,
        )
        outcome.narrative = self.build_prospective_narrative(outcome)
        return outcome

    def propose_action(
        self,
        current_goal: str,
        current_state: TheoryState,
        current_inputs: Optional[TheoryInputs] = None,
    ) -> CounterfactualOutcome:
        current_inputs = current_inputs or TheoryInputs()
        candidates = self._goal_candidates(current_goal)
        outcomes: List[CounterfactualOutcome] = []
        for action in candidates:
            outcome = self.simulate_action(current_state, current_inputs, action)
            outcomes.append(outcome)

        best = min(outcomes, key=lambda outcome: outcome.expected_free_energy)
        return best

    def learn_from_outcome(
        self,
        previous_state: TheoryState,
        inputs: TheoryInputs,
        actual_action: str,
        actual_state: TheoryState,
        prior_goal: str,
    ) -> None:
        actual_score = self.evaluate_state(actual_state)
        candidates = self._goal_candidates(prior_goal)
        regrets: List[float] = []

        for action in candidates:
            imagined = self.simulate_action(previous_state, inputs, action)
            regret = abs(imagined.predicted_score - actual_score)
            imagined.regret = regret
            regrets.append(regret)

        self.last_regret = clamp(sum(regrets) / max(1, len(regrets)), 0.0, 1.0)
        self.regret_history.append(self.last_regret)
