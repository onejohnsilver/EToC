from dataclasses import dataclass
from typing import Dict


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass
class SomaticState:
    """Simple embodied state that feeds back into affect and action choice.

    All values are normalized to [0.0, 1.0].
    - heart_rate: 0.0 (slow) .. 1.0 (racing)
    - muscle_tension: 0.0 (relaxed) .. 1.0 (tense)
    - energy: 1.0 (full) .. 0.0 (depleted)
    - fatigue: 0.0 (fresh) .. 1.0 (exhausted)
    - temperature: 0.0 (cold) .. 1.0 (hot)
    """
    heart_rate: float = 0.45
    muscle_tension: float = 0.20
    energy: float = 1.00
    fatigue: float = 0.00
    temperature: float = 0.50
    metabolic_reserve: float = 1.00
    hydration: float = 1.00
    oxygenation: float = 1.00
    immune_load: float = 0.00
    neural_energy: float = 1.00
    exertion_timer: int = 0

    def reservoir_deviation(self) -> float:
        """Weighted multi-reservoir deviation from viable physiological bounds."""
        return clamp(
            0.30 * (1.0 - self.metabolic_reserve)
            + 0.15 * (1.0 - self.hydration)
            + 0.25 * (1.0 - self.oxygenation)
            + 0.15 * self.immune_load
            + 0.15 * (1.0 - self.neural_energy),
            0.0,
            1.0,
        )

    def cognitive_capacity(self) -> float:
        """Capacity available for recursive/narrative cognition."""
        return clamp(
            0.45 * self.neural_energy
            + 0.35 * self.metabolic_reserve
            + 0.20 * self.oxygenation
            - 0.25 * self.fatigue
            - 0.15 * self.immune_load,
            0.0,
            1.0,
        )

    def update(self, threat: float, action: str, safe: bool, dt: float = 1.0) -> None:
        """Update somatic markers from environmental threat and recent action.

        - threat raises heart rate and tension
        - active/exerting actions increase temperature and exertion_timer
        - safe states recover energy and reduce fatigue
        """
        # Heart rate increases with threat and low energy
        hr_increase = 0.45 * threat + 0.12 * (1.0 - self.energy)
        if action in {"defend", "withdraw", "explore"}:
            hr_increase += 0.08
        elif action in {"plan", "reappraise", "model_self", "reflect"}:
            hr_increase += 0.02
        self.heart_rate = clamp(self.heart_rate + hr_increase * dt, 0.0, 1.0)

        # Muscle tension reacts to action and threat
        tension_increase = 0.30 * threat
        if action in {"defend", "withdraw"}:
            tension_increase += 0.12
        elif action in {"explore", "coordinate", "support", "bond"}:
            tension_increase += 0.06
        elif action in {"plan", "reappraise", "model_self", "reflect"}:
            tension_increase += 0.02
        self.muscle_tension = clamp(self.muscle_tension + tension_increase * dt, 0.0, 1.0)

        # Temperature slightly rises with exertion, cools when resting
        if action in {"defend", "withdraw", "explore"}:
            self.temperature = clamp(self.temperature + 0.01 * dt, 0.0, 1.0)
            self.exertion_timer += 1
        else:
            self.temperature = clamp(self.temperature - 0.008 * dt, 0.0, 1.0)
            self.exertion_timer = max(0, self.exertion_timer - 1)

        # Recovery if environment is safe
        if safe and threat < 0.25:
            recovery_bonus = 0.08 * (1.0 - self.energy)
            self.energy = clamp(self.energy + recovery_bonus, 0.0, 1.0)
            self.fatigue = clamp(self.fatigue - 0.06 * dt, 0.0, 1.0)
            self.metabolic_reserve = clamp(self.metabolic_reserve + 0.03 * dt, 0.0, 1.0)
        # Otherwise energy decays slowly when active
        else:
            self.energy = clamp(self.energy - 0.01 * dt * (0.5 + threat), 0.0, 1.0)

        self.metabolic_reserve = clamp(self.metabolic_reserve - 0.006 * dt * (0.5 + threat), 0.0, 1.0)
        self.hydration = clamp(self.hydration - 0.003 * dt * (0.5 + self.temperature), 0.0, 1.0)
        self.oxygenation = clamp(self.oxygenation - 0.004 * dt * max(0.0, self.heart_rate - 0.65), 0.0, 1.0)
        self.immune_load = clamp(self.immune_load + 0.003 * dt * threat - 0.002 * dt * float(safe), 0.0, 1.0)
        self.neural_energy = clamp(self.neural_energy - 0.004 * dt * (0.5 + threat), 0.0, 1.0)

        if action in {"wait", "rest", "conserve", "reappraise", "model_self", "reflect"}:
            regulation = 0.04 if action in {"rest", "conserve"} else 0.02
            if threat < 0.60:
                self.energy = clamp(self.energy + regulation * dt, 0.0, 1.0)
                self.metabolic_reserve = clamp(self.metabolic_reserve + 0.5 * regulation * dt, 0.0, 1.0)
                self.neural_energy = clamp(self.neural_energy + 0.35 * regulation * dt, 0.0, 1.0)
                self.fatigue = clamp(self.fatigue - 0.03 * dt, 0.0, 1.0)
            self.heart_rate = clamp(self.heart_rate - 0.03 * dt, 0.0, 1.0)
            self.muscle_tension = clamp(self.muscle_tension - 0.03 * dt, 0.0, 1.0)

        # Fatigue accumulates when exertion is prolonged or energy is low
        if self.exertion_timer > 6 or self.energy < 0.30:
            self.fatigue = clamp(self.fatigue + 0.02 * dt + 0.06 * (1.0 - self.energy), 0.0, 1.0)

    def consume_energy(self, action: str) -> None:
        """Apply an immediate energy cost for the chosen action."""
        costs = {
            "defend": (0.14, 0.025, 0.05, 0.01, 0.02),
            "withdraw": (0.12, 0.020, 0.04, 0.01, 0.02),
            "explore": (0.10, 0.030, 0.03, 0.02, 0.035),
            "conserve": (-0.03, -0.025, 0.00, 0.00, -0.015),
            "rest": (-0.04, -0.025, 0.00, -0.008, -0.020),
            "plan": (0.025, 0.012, 0.00, 0.00, 0.050),
            "reappraise": (0.01, 0.006, 0.00, 0.00, 0.030),
            "support": (0.07, 0.020, 0.01, 0.005, 0.020),
            "bond": (0.05, 0.015, 0.00, 0.00, 0.015),
            "coordinate": (0.07, 0.020, 0.01, 0.005, 0.025),
            "wait": (-0.02, -0.015, 0.00, 0.00, -0.010),
            "model_self": (0.01, 0.006, 0.00, 0.00, 0.035),
            "reflect": (0.01, 0.006, 0.00, 0.00, 0.035),
        }
        energy_cost, metabolic_cost, hydration_cost, immune_delta, neural_cost = costs.get(
            action, (0.06, 0.018, 0.01, 0.005, 0.018)
        )
        fatigue_multiplier = 1.0 + (0.5 * self.fatigue) + (0.3 * (1.0 - self.energy))
        scaled_energy_cost = energy_cost * fatigue_multiplier
        self.energy = clamp(self.energy - scaled_energy_cost, 0.0, 1.0)
        self.metabolic_reserve = clamp(self.metabolic_reserve - metabolic_cost, 0.0, 1.0)
        self.hydration = clamp(self.hydration - hydration_cost, 0.0, 1.0)
        self.immune_load = clamp(self.immune_load + immune_delta, 0.0, 1.0)
        self.neural_energy = clamp(self.neural_energy - neural_cost, 0.0, 1.0)
        if scaled_energy_cost < 0:
            self.fatigue = clamp(self.fatigue + scaled_energy_cost, 0.0, 1.0)
        if scaled_energy_cost > 0:
            self.exertion_timer += 1
        if self.energy < 0.20 or self.cognitive_capacity() < 0.20:
            self.fatigue = clamp(self.fatigue + 0.04, 0.0, 1.0)

    def as_dict(self) -> Dict[str, float]:
        return {
            "heart_rate": self.heart_rate,
            "muscle_tension": self.muscle_tension,
            "energy": self.energy,
            "fatigue": self.fatigue,
            "temperature": self.temperature,
            "metabolic_reserve": self.metabolic_reserve,
            "hydration": self.hydration,
            "oxygenation": self.oxygenation,
            "immune_load": self.immune_load,
            "neural_energy": self.neural_energy,
            "reservoir_deviation": self.reservoir_deviation(),
            "cognitive_capacity": self.cognitive_capacity(),
        }


def classify_somatic_emotion(somatic: SomaticState, valence: float) -> str:
    """Return a simple emotion label influenced by somatic markers and valence."""
    if somatic.heart_rate > 0.75 and valence < 0.45:
        return "fear"
    if somatic.heart_rate > 0.70 and valence >= 0.45:
        return "excitement"
    if somatic.fatigue > 0.60 and valence < 0.55:
        return "tired_cautious"
    if somatic.energy < 0.25:
        return "fatigued"
    if somatic.heart_rate < 0.40 and valence > 0.60:
        return "calm"
    return "neutral"
