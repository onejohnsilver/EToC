#!/usr/bin/env python3
"""
core_memory.py

Persistence layer for the Evolutionary Survival Theory of Consciousness.

This file adds:
    - memory storage across time
    - recursive history summaries
    - identity continuity signals
    - retrieval of recent state traces

It does not redefine the theory equations.
It only manages what the system remembers and how memory shapes continuity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from core_types import TheoryState


# ============================================================
# Memory records
# ============================================================


@dataclass(frozen=True)
class MemoryTrace:
    """A compact record of one update step."""

    step_index: int
    survival_loss: float
    boundary_integrity: float
    prediction_error: float
    self_model_depth: float
    social_model_depth: float
    recursive_integration: float
    subjective_experience: float
    consciousness_index: float
    note: str = ""


@dataclass
class IdentitySummary:
    """Compressed continuity state derived from memory."""

    identity_stability: float = 0.0
    continuity_strength: float = 0.0
    coherence: float = 0.0
    trust_history: float = 0.0
    threat_history: float = 0.0
    self_narrative_strength: float = 0.0
    social_narrative_strength: float = 0.0


@dataclass
class MemoryBank:
    """
    Persistent memory container.

    The memory bank stores raw traces and maintains a rolling recursive summary.
    The summary acts like a simple identity model over time.
    """

    max_traces: int = 128
    traces: List[MemoryTrace] = field(default_factory=list)
    identity: IdentitySummary = field(default_factory=IdentitySummary)

    def add_trace(self, trace: MemoryTrace) -> None:
        self.traces.append(trace)
        self.traces = self.traces[-self.max_traces :]
        self.identity = update_identity(self.identity, self.traces)

    def latest(self) -> Optional[MemoryTrace]:
        return self.traces[-1] if self.traces else None

    def recent(self, n: int = 5) -> List[MemoryTrace]:
        return self.traces[-max(0, n) :]

    def to_state_memory(self) -> List[Dict[str, float]]:
        """Convert to the loose dictionary style used by TheoryState.memory."""
        return [
            {
                "step_index": float(t.step_index),
                "survival_loss": t.survival_loss,
                "boundary_integrity": t.boundary_integrity,
                "prediction_error": t.prediction_error,
                "self_model_depth": t.self_model_depth,
                "social_model_depth": t.social_model_depth,
                "recursive_integration": t.recursive_integration,
                "subjective_experience": t.subjective_experience,
                "consciousness_index": t.consciousness_index,
            }
            for t in self.traces
        ]


# ============================================================
# Trace creation
# ============================================================


def make_trace(state: TheoryState, note: str = "") -> MemoryTrace:
    """Create a compact memory trace from the current theory state."""
    return MemoryTrace(
        step_index=int(state.step_index),
        survival_loss=float(state.survival_loss),
        boundary_integrity=float(state.boundary_integrity),
        prediction_error=float(state.prediction_error),
        self_model_depth=float(state.self_model_depth),
        social_model_depth=float(state.social_model_depth),
        recursive_integration=float(state.recursive_integration),
        subjective_experience=float(state.subjective_experience),
        consciousness_index=float(state.consciousness_index),
        note=note,
    )


# ============================================================
# Continuity / identity math
# ============================================================


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _trend(values: Sequence[float]) -> float:
    """
    Simple signed trend in [-1, 1].

    Positive means increasing over the recent window.
    Negative means decreasing.
    """
    if len(values) < 2:
        return 0.0
    start = values[0]
    end = values[-1]
    span = max(1e-9, max(values) - min(values))
    return max(-1.0, min(1.0, (end - start) / span))


def update_identity(identity: IdentitySummary, traces: Sequence[MemoryTrace]) -> IdentitySummary:
    """
    Update recursive identity continuity from memory.

    The idea:
        - stable survival and boundary history increase identity stability
        - consistent self-model and recursion increase continuity
        - social memory contributes to narratable identity
        - persistent threat reduces coherence
    """
    if not traces:
        return IdentitySummary()

    recent = list(traces[-32:])
    survival_vals = [t.survival_loss for t in recent]
    boundary_vals = [t.boundary_integrity for t in recent]
    self_vals = [t.self_model_depth for t in recent]
    social_vals = [t.social_model_depth for t in recent]
    rec_vals = [t.recursive_integration for t in recent]
    subj_vals = [t.subjective_experience for t in recent]
    conc_vals = [t.consciousness_index for t in recent]
    pred_vals = [t.prediction_error for t in recent]

    avg_survival = _mean(survival_vals)
    avg_boundary = _mean(boundary_vals)
    avg_self = _mean(self_vals)
    avg_social = _mean(social_vals)
    avg_rec = _mean(rec_vals)
    avg_subj = _mean(subj_vals)
    avg_conc = _mean(conc_vals)
    avg_pred = _mean(pred_vals)

    stability = max(0.0, min(1.0, 0.55 * avg_boundary + 0.45 * (1.0 / (1.0 + avg_survival))))
    continuity = max(0.0, min(1.0, 0.45 * avg_self + 0.35 * avg_rec + 0.20 * avg_subj))
    coherence = max(0.0, min(1.0, 0.40 * avg_conc + 0.30 * avg_boundary + 0.30 * (1.0 - avg_pred)))
    trust_history = max(0.0, min(1.0, avg_social))
    threat_history = max(0.0, min(1.0, avg_survival))

    # Recursive narrative strength emerges from stability over time.
    self_narrative = max(0.0, min(1.0, 0.50 * continuity + 0.50 * stability))
    social_narrative = max(0.0, min(1.0, 0.50 * trust_history + 0.50 * coherence))

    # Identity stability combines continuity, coherence, and stability of boundary/survival.
    identity_stability = max(0.0, min(1.0, 0.40 * stability + 0.35 * continuity + 0.25 * coherence))

    return IdentitySummary(
        identity_stability=identity_stability,
        continuity_strength=continuity,
        coherence=coherence,
        trust_history=trust_history,
        threat_history=threat_history,
        self_narrative_strength=self_narrative,
        social_narrative_strength=social_narrative,
    )


# ============================================================
# Memory manager
# ============================================================


class MemoryManager:
    """
    Higher-level memory interface.

    Later modules should use this instead of touching the raw trace list directly.
    It keeps persistence and identity continuity in one place.
    """

    def __init__(self, max_traces: int = 128):
        self.bank = MemoryBank(max_traces=max_traces)

    def store(self, state: TheoryState, note: str = "") -> MemoryTrace:
        trace = make_trace(state, note=note)
        self.bank.add_trace(trace)
        return trace

    def recent_traces(self, n: int = 5) -> List[MemoryTrace]:
        return self.bank.recent(n)

    def identity_summary(self) -> IdentitySummary:
        return self.bank.identity

    def export_state_memory(self) -> List[Dict[str, float]]:
        return self.bank.to_state_memory()

    def inject_into_state(self, state: TheoryState) -> TheoryState:
        """Copy memory traces into a TheoryState for compatibility with other files."""
        state.memory = self.export_state_memory()
        return state

    def sync_from_state(self, state: TheoryState) -> None:
        """Load state memory into the bank when needed."""
        self.bank.traces = [
            MemoryTrace(
                step_index=int(item.get("step_index", 0.0)),
                survival_loss=float(item.get("survival_loss", 0.0)),
                boundary_integrity=float(item.get("boundary_integrity", 0.0)),
                prediction_error=float(item.get("prediction_error", 0.0)),
                self_model_depth=float(item.get("self_model_depth", 0.0)),
                social_model_depth=float(item.get("social_model_depth", 0.0)),
                recursive_integration=float(item.get("recursive_integration", 0.0)),
                subjective_experience=float(item.get("subjective_experience", 0.0)),
                consciousness_index=float(item.get("consciousness_index", 0.0)),
                note=str(item.get("note", "")),
            )
            for item in state.memory[-self.bank.max_traces :]
        ]
        self.bank.identity = update_identity(self.bank.identity, self.bank.traces)


# ============================================================
# Convenience functions
# ============================================================


def continuity_score(traces: Sequence[MemoryTrace]) -> float:
    """A compact continuity score derived from memory history."""
    if not traces:
        return 0.0
    recent = list(traces[-16:])
    self_vals = [t.self_model_depth for t in recent]
    social_vals = [t.social_model_depth for t in recent]
    rec_vals = [t.recursive_integration for t in recent]
    subj_vals = [t.subjective_experience for t in recent]
    return max(0.0, min(1.0, 0.35 * _mean(self_vals) + 0.25 * _mean(social_vals) + 0.25 * _mean(rec_vals) + 0.15 * _mean(subj_vals)))


def recursion_across_time(traces: Sequence[MemoryTrace]) -> float:
    """Measures whether recursion is sustained across recent time steps."""
    if not traces:
        return 0.0
    recent = list(traces[-16:])
    rec_vals = [t.recursive_integration for t in recent]
    return max(0.0, min(1.0, 0.5 * _mean(rec_vals) + 0.5 * max(0.0, _trend(rec_vals))))
