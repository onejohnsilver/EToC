#!/usr/bin/env python3
"""
core_memory.py

Persistence layer for the Evolutionary Survival Theory of Consciousness.

Modifications for Operator Testing:
    - Dual-track memory storage (Chronological Queue + Salience Bank).
    - Affectively weighted recursive history summaries.
    - Identity continuity signals gated by survival priority and orthogonal cost.
    - Strict non-breaking compatibility with TheoryState serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

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

    The memory bank utilizes a Dual-Track system:
    1. A standard rolling chronological window (max_traces).
    2. A Salience Bank that retains high-threat, high-error events indefinitely 
       to prevent catastrophic forgetting of survival-critical data.
    """

    max_traces: int = 128
    max_salient: int = 64
    traces: List[MemoryTrace] = field(default_factory=list)
    salient_traces: List[MemoryTrace] = field(default_factory=list)
    identity: IdentitySummary = field(default_factory=IdentitySummary)

    def add_trace(self, trace: MemoryTrace) -> None:
        # Standard chronological queue
        self.traces.append(trace)
        self.traces = self.traces[-self.max_traces :]

        # Salience Bank: Retain high-threat or high-error traces as survival anchors.
        if trace.survival_loss > 0.40 or trace.prediction_error > 0.60 or trace.subjective_experience > 0.80:
            self.salient_traces.append(trace)

        # Apply exponential decay to salient traces based on age.
        # Older traumatic anchors fade over time so recovery is possible.
        decayed_salient: List[MemoryTrace] = []
        current_step = trace.step_index
        for st in self.salient_traces:
            age = max(0, current_step - st.step_index)
            decay_factor = max(0.0, 1.0 - (age * 0.0015))
            if decay_factor > 0.05:
                decayed_salient.append(st)

        self.salient_traces = decayed_salient[-self.max_salient :]
        self.identity = update_identity(self.identity, self.traces, self.salient_traces)

    def latest(self) -> Optional[MemoryTrace]:
        return self.traces[-1] if self.traces else None

    def recent(self, n: int = 5) -> List[MemoryTrace]:
        return self.traces[-max(0, n) :]

    def salient(self, n: int = 5) -> List[MemoryTrace]:
        """Exposes the most critical survival anchors for predictive allostasis."""
        return self.salient_traces[-max(0, n) :]

    def to_state_memory(self) -> List[Dict[str, float]]:
        """
        Convert to the loose dictionary style used by TheoryState.memory.
        Strictly serializes ONLY the chronological traces to prevent 
        breaking expected array sizes in the core engine.
        """
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


def _weighted_mean(traces: Sequence[MemoryTrace], extract_fn: Callable[[MemoryTrace], float]) -> float:
    """
    Computes a recency-weighted average for identity summaries.
    Recent traces have stronger influence while past experiences fade naturally.
    """
    if not traces:
        return 0.0
    
    total_weight = 0.0
    weighted_sum = 0.0
    n = len(traces)
    
    for i, t in enumerate(traces):
        recency_factor = 0.85 ** (n - i - 1)
        weight = recency_factor
        val = extract_fn(t)
        weighted_sum += val * weight
        total_weight += weight
        
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def _trend(values: Sequence[float]) -> float:
    """Simple signed trend in [-1, 1]."""
    if len(values) < 2:
        return 0.0
    start = values[0]
    end = values[-1]
    span = max(1e-9, max(values) - min(values))
    return max(-1.0, min(1.0, (end - start) / span))


def update_identity(
    identity: IdentitySummary, 
    traces: Sequence[MemoryTrace], 
    salient_traces: Sequence[MemoryTrace] = ()
) -> IdentitySummary:
    """
    Update recursive identity continuity from memory utilizing affective weighting.
    Combines recent chronology with permanent salient survival anchors.
    """
    if not traces:
        return IdentitySummary()

    # Pool recent memory with historical salient anchors, removing duplicate step indices
    recent = list(traces[-32:])
    combined_pool = {t.step_index: t for t in list(salient_traces) + recent}.values()
    active_memory = list(combined_pool)

    # Use affectively weighted means instead of flat mathematical smoothing
    avg_survival = _weighted_mean(active_memory, lambda t: t.survival_loss)
    avg_boundary = _weighted_mean(active_memory, lambda t: t.boundary_integrity)
    avg_self = _weighted_mean(active_memory, lambda t: t.self_model_depth)
    avg_social = _weighted_mean(active_memory, lambda t: t.social_model_depth)
    avg_rec = _weighted_mean(active_memory, lambda t: t.recursive_integration)
    avg_subj = _weighted_mean(active_memory, lambda t: t.subjective_experience)
    avg_conc = _weighted_mean(active_memory, lambda t: t.consciousness_index)
    avg_pred = _weighted_mean(active_memory, lambda t: t.prediction_error)

    stability = max(0.0, min(1.0, 0.55 * avg_boundary + 0.45 * (1.0 / (1.0 + avg_survival))))
    continuity = max(0.0, min(1.0, 0.45 * avg_self + 0.35 * avg_rec + 0.20 * avg_subj))
    
    # Coherence sharply drops if prediction errors consistently remain high
    coherence = max(0.0, min(1.0, 0.40 * avg_conc + 0.30 * avg_boundary + 0.30 * (1.0 - avg_pred)))
    
    trust_history = max(0.0, min(1.0, avg_social))
    threat_history = max(0.0, min(1.0, avg_survival))

    self_narrative = max(0.0, min(1.0, 0.50 * continuity + 0.50 * stability))
    social_narrative = max(0.0, min(1.0, 0.50 * trust_history + 0.50 * coherence))

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
    """

    def __init__(self, max_traces: int = 128, disable_salience: bool = False, disable_identity: bool = False):
        self.bank = MemoryBank(max_traces=max_traces)
        self.disable_salience = disable_salience
        self.disable_identity = disable_identity

    def store(self, state: TheoryState, note: str = "") -> MemoryTrace:
        trace = make_trace(state, note=note)
        self.bank.add_trace(trace)
        return trace

    def recent_traces(self, n: int = 5) -> List[MemoryTrace]:
        return self.bank.recent(n)
        
    def salient_traces(self, n: int = 5) -> List[MemoryTrace]:
        """Provides access to the most severe historical events for active inference."""
        if self.disable_salience:
            return []
        return self.bank.salient(n)

    def identity_summary(self) -> IdentitySummary:
        if self.disable_identity:
            return IdentitySummary()
        return self.bank.identity

    def export_state_memory(self) -> List[Dict[str, float]]:
        return self.bank.to_state_memory()

    def inject_into_state(self, state: TheoryState) -> TheoryState:
        """Copy chronological memory traces into a TheoryState."""
        state.memory = self.export_state_memory()
        return state

    def sync_from_state(self, state: TheoryState) -> None:
        """Load state memory into the bank when needed, reconstructing salience."""
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
        
        # Re-evaluate loaded traces for the salience bank
        self.bank.salient_traces = [
            t for t in self.bank.traces 
            if t.survival_loss > 0.40 or t.prediction_error > 0.60 or t.subjective_experience > 0.80
        ][-self.bank.max_salient :]
        
        self.bank.identity = update_identity(self.bank.identity, self.bank.traces, self.bank.salient_traces)

    # ----------------------------
    # Narrative-friendly helpers
    # ----------------------------
    def narrative_frame(self, n_traces: int = 12):
        """Build a NarrativeFrame from the most recent `n_traces`.

        This is a thin integration point with `core_narrative` and keeps
        the memory manager as the authoritative source of chronological
        traces.
        """
        try:
            # import locally to avoid circular imports at module load time
            from core_narrative import build_narrative_from_traces
        except Exception:
            return None

        traces = self.recent_traces(n_traces)
        return build_narrative_from_traces(traces, max_sentences=n_traces)

    def narrative_summary(self, short_sentences: int = 3, n_traces: int = 12) -> Tuple[str, float]:
        """Return a short textual summary and coherence score for recent memory."""
        frame = self.narrative_frame(n_traces=n_traces)
        if frame is None:
            return ("Narrative unavailable.", 0.0)
        try:
            from core_narrative import summarize_narrative

            return (summarize_narrative(frame, max_sentences=short_sentences), frame.coherence)
        except Exception:
            return ("Narrative construction failed.", frame.coherence)


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
    return max(0.0, min(1.0, 0.35 * _mean_standard(self_vals) + 0.25 * _mean_standard(social_vals) + 0.25 * _mean_standard(rec_vals) + 0.15 * _mean_standard(subj_vals)))

def _mean_standard(values: Sequence[float]) -> float:
    """Standard unweighted mean for simple convenience functions."""
    if not values:
        return 0.0
    return sum(values) / len(values)

def recursion_across_time(traces: Sequence[MemoryTrace]) -> float:
    """Measures whether recursion is sustained across recent time steps."""
    if not traces:
        return 0.0
    recent = list(traces[-16:])
    rec_vals = [t.recursive_integration for t in recent]
    return max(0.0, min(1.0, 0.5 * _mean_standard(rec_vals) + 0.5 * max(0.0, _trend(rec_vals))))