#!/usr/bin/env python3
"""
core_metrics.py

Metrics layer for the Evolutionary Survival Theory of Consciousness.

This file turns state and memory into readable summary scores for analysis.
It does not run the simulation and it does not define the equations.
It only measures the behavior of the evolving system.

Primary purposes:
    - summarize survival, prediction, affect, self-model, social model, recursion
    - expose consciousness trend metrics
    - support ablation comparisons
    - provide stable outputs for later plotting and evaluation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from core_types import TheoryState
from core_memory import MemoryTrace, IdentitySummary


# ============================================================
# Small helpers
# ============================================================


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def delta(values: Sequence[float]) -> float:
    """Simple signed change from first to last value."""
    if len(values) < 2:
        return 0.0
    return values[-1] - values[0]


def trend(values: Sequence[float]) -> float:
    """
    Normalized trend indicator in [-1, 1].

    Positive means increasing over time.
    Negative means decreasing over time.
    """
    if len(values) < 2:
        return 0.0
    lo = min(values)
    hi = max(values)
    span = max(1e-9, hi - lo)
    return clamp((values[-1] - values[0]) / span, -1.0, 1.0)


# ============================================================
# Summary dataclass
# ============================================================


@dataclass(frozen=True)
class MetricSummary:
    """Compact summary of the current theory state."""

    survival_score: float
    stability_score: float
    prediction_score: float
    affect_score: float
    self_model_score: float
    social_score: float
    recursion_score: float
    experience_score: float
    consciousness_score: float
    identity_score: float
    overall_adaptation_score: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "survival_score": self.survival_score,
            "stability_score": self.stability_score,
            "prediction_score": self.prediction_score,
            "affect_score": self.affect_score,
            "self_model_score": self.self_model_score,
            "social_score": self.social_score,
            "recursion_score": self.recursion_score,
            "experience_score": self.experience_score,
            "consciousness_score": self.consciousness_score,
            "identity_score": self.identity_score,
            "overall_adaptation_score": self.overall_adaptation_score,
        }


# ============================================================
# Core metric computations
# ============================================================


def survival_score(state: TheoryState) -> float:
    """Higher viability and lower survival loss imply better survival."""
    score = 0.60 * state.viability + 0.40 * (1.0 - clamp(state.survival_loss, 0.0, 1.0))
    return clamp(score, 0.0, 1.0)


def stability_score(state: TheoryState) -> float:
    """Boundary integrity and low thermodynamic load indicate stable organization."""
    score = 0.55 * state.boundary_integrity + 0.45 * (1.0 - clamp(state.thermodynamic_load, 0.0, 1.0))
    return clamp(score, 0.0, 1.0)


def prediction_score(state: TheoryState) -> float:
    """Precision minus error as a simple predictive quality score."""
    score = 0.55 * state.predictive_precision + 0.45 * (1.0 - state.prediction_error)
    return clamp(score, 0.0, 1.0)


def affect_score(state: TheoryState) -> float:
    """Valence and arousal combined into a single affective readiness score."""
    score = 0.55 * state.affect_valence + 0.45 * state.affect_arousal
    return clamp(score, 0.0, 1.0)


def self_model_score(state: TheoryState) -> float:
    return clamp(state.self_model_depth, 0.0, 1.0)


def social_score(state: TheoryState) -> float:
    return clamp(state.social_model_depth, 0.0, 1.0)


def recursion_score(state: TheoryState) -> float:
    return clamp(state.recursive_integration, 0.0, 1.0)


def experience_score(state: TheoryState) -> float:
    return clamp(state.subjective_experience, 0.0, 1.0)


def consciousness_score(state: TheoryState) -> float:
    return clamp(state.consciousness_index, 0.0, 1.0)


def identity_score(identity: IdentitySummary) -> float:
    """
    Identity is the continuity of the system over time.
    Higher identity stability, continuity, and coherence raise the score.
    """
    score = (
        0.35 * identity.identity_stability
        + 0.25 * identity.continuity_strength
        + 0.20 * identity.coherence
        + 0.10 * identity.self_narrative_strength
        + 0.10 * identity.social_narrative_strength
    )
    return clamp(score, 0.0, 1.0)


def overall_adaptation_score(state: TheoryState, identity: IdentitySummary) -> float:
    """
    A single high-level score for the current architecture.

    This is intentionally not a replacement for the layer scores.
    It is only a convenience summary.
    """
    score = (
        0.18 * survival_score(state)
        + 0.12 * stability_score(state)
        + 0.12 * prediction_score(state)
        + 0.10 * affect_score(state)
        + 0.10 * self_model_score(state)
        + 0.10 * social_score(state)
        + 0.12 * recursion_score(state)
        + 0.08 * experience_score(state)
        + 0.10 * consciousness_score(state)
        + 0.08 * identity_score(identity)
    )
    return clamp(score, 0.0, 1.0)


# ============================================================
# Time-series metrics from traces
# ============================================================


def metric_trend(traces: Sequence[MemoryTrace]) -> Dict[str, float]:
    """Compute simple trends across recent memory."""
    if not traces:
        return {
            "survival_loss_trend": 0.0,
            "boundary_integrity_trend": 0.0,
            "prediction_error_trend": 0.0,
            "self_model_trend": 0.0,
            "social_model_trend": 0.0,
            "recursion_trend": 0.0,
            "experience_trend": 0.0,
            "consciousness_trend": 0.0,
        }

    surv = [t.survival_loss for t in traces]
    bound = [t.boundary_integrity for t in traces]
    pred = [t.prediction_error for t in traces]
    selfv = [t.self_model_depth for t in traces]
    social = [t.social_model_depth for t in traces]
    rec = [t.recursive_integration for t in traces]
    exp = [t.subjective_experience for t in traces]
    conc = [t.consciousness_index for t in traces]

    return {
        "survival_loss_trend": trend(surv),
        "boundary_integrity_trend": trend(bound),
        "prediction_error_trend": trend(pred),
        "self_model_trend": trend(selfv),
        "social_model_trend": trend(social),
        "recursion_trend": trend(rec),
        "experience_trend": trend(exp),
        "consciousness_trend": trend(conc),
    }


def metric_averages(traces: Sequence[MemoryTrace]) -> Dict[str, float]:
    """Mean values across recent memory."""
    if not traces:
        return {
            "avg_survival_loss": 0.0,
            "avg_boundary_integrity": 0.0,
            "avg_prediction_error": 0.0,
            "avg_self_model_depth": 0.0,
            "avg_social_model_depth": 0.0,
            "avg_recursive_integration": 0.0,
            "avg_subjective_experience": 0.0,
            "avg_consciousness_index": 0.0,
        }

    return {
        "avg_survival_loss": mean([t.survival_loss for t in traces]),
        "avg_boundary_integrity": mean([t.boundary_integrity for t in traces]),
        "avg_prediction_error": mean([t.prediction_error for t in traces]),
        "avg_self_model_depth": mean([t.self_model_depth for t in traces]),
        "avg_social_model_depth": mean([t.social_model_depth for t in traces]),
        "avg_recursive_integration": mean([t.recursive_integration for t in traces]),
        "avg_subjective_experience": mean([t.subjective_experience for t in traces]),
        "avg_consciousness_index": mean([t.consciousness_index for t in traces]),
    }


# ============================================================
# Full summary helpers
# ============================================================


def summarize_state(state: TheoryState, identity: IdentitySummary) -> MetricSummary:
    """One-stop summary of the current theory state."""
    return MetricSummary(
        survival_score=survival_score(state),
        stability_score=stability_score(state),
        prediction_score=prediction_score(state),
        affect_score=affect_score(state),
        self_model_score=self_model_score(state),
        social_score=social_score(state),
        recursion_score=recursion_score(state),
        experience_score=experience_score(state),
        consciousness_score=consciousness_score(state),
        identity_score=identity_score(identity),
        overall_adaptation_score=overall_adaptation_score(state, identity),
    )


def summarize_traces(traces: Sequence[MemoryTrace]) -> Dict[str, float]:
    """Combine averages and trends for reporting."""
    out = {}
    out.update(metric_averages(traces))
    out.update(metric_trend(traces))
    return out


# ============================================================
# Ablation comparison helpers
# ============================================================


def compare_summaries(
    a: MetricSummary,
    b: MetricSummary,
    label_a: str = "A",
    label_b: str = "B",
) -> Dict[str, float]:
    """Compare two metric summaries as simple differences (A - B)."""
    return {
        f"{label_a}_minus_{label_b}_survival": a.survival_score - b.survival_score,
        f"{label_a}_minus_{label_b}_stability": a.stability_score - b.stability_score,
        f"{label_a}_minus_{label_b}_prediction": a.prediction_score - b.prediction_score,
        f"{label_a}_minus_{label_b}_affect": a.affect_score - b.affect_score,
        f"{label_a}_minus_{label_b}_self_model": a.self_model_score - b.self_model_score,
        f"{label_a}_minus_{label_b}_social": a.social_score - b.social_score,
        f"{label_a}_minus_{label_b}_recursion": a.recursion_score - b.recursion_score,
        f"{label_a}_minus_{label_b}_experience": a.experience_score - b.experience_score,
        f"{label_a}_minus_{label_b}_consciousness": a.consciousness_score - b.consciousness_score,
        f"{label_a}_minus_{label_b}_identity": a.identity_score - b.identity_score,
        f"{label_a}_minus_{label_b}_overall": a.overall_adaptation_score - b.overall_adaptation_score,
    }


# ============================================================
# Diagnostic ranking helpers
# ============================================================


def rank_layers(state: TheoryState, identity: IdentitySummary) -> List[Tuple[str, float]]:
    """
    Return a simple ranking of layer scores from highest to lowest.
    Useful for debugging which parts are strongest at the moment.
    """
    scores = [
        ("survival", survival_score(state)),
        ("stability", stability_score(state)),
        ("prediction", prediction_score(state)),
        ("affect", affect_score(state)),
        ("self_model", self_model_score(state)),
        ("social", social_score(state)),
        ("recursion", recursion_score(state)),
        ("experience", experience_score(state)),
        ("consciousness", consciousness_score(state)),
        ("identity", identity_score(identity)),
    ]
    return sorted(scores, key=lambda item: item[1], reverse=True)
