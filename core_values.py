#!/usr/bin/env python3
"""
core_values.py

Intrinsic value system and affective learning for the Evolutionary Survival Theory of Consciousness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass
class ValueSystem:
    survival_weight: float = 0.28
    autonomy_weight: float = 0.18
    belonging_weight: float = 0.20
    competence_weight: float = 0.17
    meaning_weight: float = 0.17
    satisfaction: Dict[str, float] = field(default_factory=lambda: {
        "survival": 0.75,
        "autonomy": 0.60,
        "belonging": 0.50,
        "competence": 0.55,
        "meaning": 0.45,
    })
    history: List[Dict[str, float]] = field(default_factory=list)
    learning_rate: float = 0.08
    exploration_bias: float = 0.12

    def _value_importance(self, value_name: str) -> float:
        return {
            "survival": self.survival_weight,
            "autonomy": self.autonomy_weight,
            "belonging": self.belonging_weight,
            "competence": self.competence_weight,
            "meaning": self.meaning_weight,
        }.get(value_name, 0.0)

    def evaluate_event(
        self,
        event: str,
        threat_level: float,
        social_support: float,
        uncertainty: float,
    ) -> Dict[str, float]:
        survival = clamp(1.0 - threat_level, 0.0, 1.0)
        autonomy = clamp(1.0 - uncertainty + 0.10 * social_support, 0.0, 1.0)
        belonging = clamp(0.45 * social_support + 0.40 * (1.0 - threat_level) + 0.15 * autonomy, 0.0, 1.0)
        competence = clamp(0.65 - 0.55 * uncertainty + 0.20 * (1.0 - threat_level), 0.0, 1.0)
        meaning = clamp(0.40 + 0.30 * social_support + 0.20 * autonomy + 0.10 * survival, 0.0, 1.0)
        appraisal = {
            "survival": survival,
            "autonomy": autonomy,
            "belonging": belonging,
            "competence": competence,
            "meaning": meaning,
        }
        self.history.append({"event": event, **appraisal})
        self.history = self.history[-64:]
        return appraisal

    def appraise_from_threats(self, appraisal: Dict[str, float]) -> tuple[str, float]:
        survival = appraisal.get("survival", 0.0)
        belonging = appraisal.get("belonging", 0.0)
        autonomy = appraisal.get("autonomy", 0.0)
        competence = appraisal.get("competence", 0.0)
        meaning = appraisal.get("meaning", 0.0)

        if survival < 0.30:
            return "fear", clamp(0.4 + 0.9 * (1.0 - survival), 0.0, 1.0)
        if belonging < 0.35:
            return "lonely", clamp(0.3 + 0.7 * (1.0 - belonging), 0.0, 1.0)
        if autonomy < 0.35:
            return "frustrated", clamp(0.2 + 0.6 * (1.0 - autonomy), 0.0, 1.0)
        if competence < 0.40:
            return "uncertain", clamp(0.2 + 0.5 * (1.0 - competence), 0.0, 1.0)
        if meaning < 0.45:
            return "questioning", clamp(0.2 + 0.5 * (1.0 - meaning), 0.0, 1.0)
        if survival > 0.75 and belonging > 0.55:
            return "content", clamp(0.15 + 0.5 * min(survival, belonging), 0.0, 1.0)
        return "curious", clamp(0.2 + 0.6 * (autonomy + competence) / 2.0, 0.0, 1.0)

    def update_from_outcome(
        self,
        event: str,
        emotion_label: str,
        intensity: float,
    ) -> None:
        recent_frequency = sum(1 for h in self.history[-20:] if h.get("emotion") == emotion_label)
        extinction_factor = 1.0 / (1.0 + 0.2 * recent_frequency)
        adaptive_lr = self.learning_rate * extinction_factor
        adjustment = (
            adaptive_lr * intensity
            if emotion_label in {"fear", "lonely", "frustrated", "uncertain"}
            else adaptive_lr * (1.0 - intensity)
        )

        for key, current in self.satisfaction.items():
            if emotion_label in {"fear", "lonely", "frustrated", "uncertain"}:
                self.satisfaction[key] = clamp(current - adjustment * self._value_importance(key), 0.0, 1.0)
            else:
                self.satisfaction[key] = clamp(current + adjustment * self._value_importance(key), 0.0, 1.0)

        self.history.append({"event": event, "emotion": emotion_label, "intensity": intensity})
        self.history = self.history[-128:]

    def score_goals(
        self,
        goals: Sequence[str],
        threat: float,
        social_support: float,
        uncertainty: float,
    ) -> Dict[str, float]:
        active_values = {
            "shore_up_boundary": ["survival", "competence"],
            "reduce_threat": ["survival", "belonging"],
            "conserve_energy": ["survival", "autonomy"],
            "sample_environment": ["competence", "autonomy"],
            "update_model": ["competence", "meaning"],
            "plan_action": ["autonomy", "meaning"],
            "signal_peers": ["belonging", "meaning"],
            "coordinate": ["belonging", "competence"],
            "bond": ["belonging", "meaning"],
            "pause": ["autonomy", "survival"],
            "reappraise": ["competence", "autonomy"],
            "model_self": ["autonomy", "meaning"],
            "slow_down": ["survival", "autonomy"],
            "repair": ["survival", "competence"],
            "rest": ["survival", "autonomy"],
            "maintain_safety": ["survival", "meaning"],
        }
        appraisal = self.evaluate_event(
            event=", ".join(goals) if hasattr(goals, "__iter__") else str(goals),
            threat_level=threat,
            social_support=social_support,
            uncertainty=uncertainty,
        )
        scores: Dict[str, float] = {}
        for goal in goals:
            values = active_values.get(goal, ["survival", "competence"])
            base = sum(self.satisfaction.get(value, 0.5) * self._value_importance(value) for value in values)
            if values:
                base /= sum(self._value_importance(value) for value in values)
            horizon = 0.10 * (1.0 - threat) + 0.10 * social_support + 0.05 * (1.0 - uncertainty)
            scores[goal] = clamp(base + horizon, 0.0, 1.0)
        return scores

    def summary(self) -> Dict[str, float]:
        return {f"value_{key}": value for key, value in self.satisfaction.items()}

    def overall_score(self) -> float:
        weighted = 0.0
        for value_name, current in self.satisfaction.items():
            weighted += current * self._value_importance(value_name)
        total_weight = self.survival_weight + self.autonomy_weight + self.belonging_weight + self.competence_weight + self.meaning_weight
        return clamp(weighted / max(1e-6, total_weight), 0.0, 1.0)
