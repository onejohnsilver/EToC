#!/usr/bin/env python3
"""
core_narrative.py

Lightweight narrative construction utilities for EToC.

Provides a `NarrativeFrame` dataclass and helper to build simple
sentence-level autobiographical narratives from `MemoryTrace` lists.

This module is intentionally small and interpretable so it can be
replaced later with more sophisticated language generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from core_memory import MemoryTrace


@dataclass
class NarrativeFrame:
    """A compact autobiographical narrative built from memory traces.

    sentences: ordered list of human-readable sentences
    coherence: float in [0,1] representing a simple consistency score
    """
    sentences: List[str] = field(default_factory=list)
    coherence: float = 0.0


def _describe_event(t: MemoryTrace) -> str:
    # Simple, interpretable event labeling
    if t.survival_loss > 0.6:
        return "a severe threat"
    if t.prediction_error > 0.6:
        return "a surprising mismatch"
    if t.subjective_experience > 0.7:
        return "an intense experience"
    if t.survival_loss > 0.3:
        return "a stressful moment"
    return "a routine moment"


def _infer_emotion(t: MemoryTrace) -> str:
    # Heuristic mapping to an emotion word
    if t.survival_loss > 0.6 or t.prediction_error > 0.7:
        return "fear"
    if getattr(t, 'subjective_experience', 0.0) > 0.7:
        return "distress"
    if t.self_model_depth > 0.6 and t.recursive_integration > 0.4:
        return "reflective calm"
    if t.self_model_depth > 0.5:
        return "assured"
    return "uncertain"


def _identity_shift(prev: MemoryTrace | None, cur: MemoryTrace) -> str:
    # Describe how self-model changed between traces
    if prev is None:
        if cur.self_model_depth > 0.5:
            return "more self-aware"
        return "forming a self-model"

    delta_self = cur.self_model_depth - prev.self_model_depth
    delta_rec = cur.recursive_integration - prev.recursive_integration
    if delta_self > 0.05 or delta_rec > 0.05:
        return "growing in self-understanding"
    if delta_self < -0.05 or delta_rec < -0.05:
        return "less certain about myself"
    return "steady in my sense of self"


def build_narrative_from_traces(traces: List[MemoryTrace], max_sentences: int = 12) -> NarrativeFrame:
    """Build a simple autobiographical narrative from chronological traces.

    Returns a NarrativeFrame with sentences and a coherence score in [0,1].
    Coherence is computed as a normalized inverse of average stepwise change
    in the key self-related metrics (self_model_depth, recursive_integration).
    """
    if not traces:
        return NarrativeFrame(sentences=["No recorded experiences yet."], coherence=0.0)

    sentences: List[str] = []
    prev = None
    deltas: List[float] = []

    for t in traces[-max_sentences:]:
        ev = _describe_event(t)
        emo = _infer_emotion(t)
        shift = _identity_shift(prev, t)
        s = f"Step {t.step_index}: I experienced {ev}, felt {emo}, and became {shift}."
        sentences.append(s)

        if prev is not None:
            d_self = abs(t.self_model_depth - prev.self_model_depth)
            d_rec = abs(t.recursive_integration - prev.recursive_integration)
            deltas.append((d_self + d_rec) / 2.0)

        prev = t

    # Compute coherence: lower average deltas -> higher coherence
    if deltas:
        avg_delta = sum(deltas) / len(deltas)
        coherence = max(0.0, min(1.0, 1.0 - (avg_delta * 5.0)))
    else:
        coherence = 1.0

    return NarrativeFrame(sentences=sentences, coherence=coherence)


def summarize_narrative(frame: NarrativeFrame, max_sentences: int = 3) -> str:
    """Return a short human-readable summary from a NarrativeFrame."""
    if not frame.sentences:
        return "No narrative available."
    summary = " ".join(frame.sentences[-max_sentences:])
    return f"{summary} (coherence={frame.coherence:.2f})"
