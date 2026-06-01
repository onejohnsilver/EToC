#!/usr/bin/env python3
"""Language module for reasoning-based agent narrative generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LanguageGenerator:
    name: str
    coherence_window: int = 6
    # Track the last peer utterance mentioned to avoid repeated quoting
    last_peer_utterance: Optional[str] = None
    # Number of turns to cool down before re-mentioning the same peer utterance
    mention_cooldown: int = 2
    # Internal timer (counts down each generate call)
    _mention_timer: int = 0

    def generate(
        self,
        emotional_state: Dict[str, float],
        somatic_state: Optional[Dict[str, float]],
        primary_emotion: str,
        intended_action: str,
        action_rationale: str,
        goal: str,
        dialogue_history: List[str],
        peer_utterance: Optional[str] = None,
        recent_memory: Optional[List[str]] = None,
    ) -> str:
        # Prevent repeatedly quoting the exact same peer utterance across turns.
        suppressed = False
        original_peer = peer_utterance

        if peer_utterance:
            sanitized = self._sanitize_peer_utterance(peer_utterance)
            # If it's identical to the last mentioned and we're still in cooldown, suppress it
            if self.last_peer_utterance and sanitized == self.last_peer_utterance and self._mention_timer > 0:
                peer_utterance = None
                suppressed = True
            else:
                peer_utterance = sanitized

        # Build utterance pieces
        emotion_desc = self._describe_emotion(emotional_state, primary_emotion)

        # Integrate somatic cues into the emotion description when available
        if somatic_state:
            try:
                fatigue = float(somatic_state.get("fatigue", 0.0))
                energy = float(somatic_state.get("energy", 1.0))
                if fatigue > 0.65:
                    emotion_desc = emotion_desc + " — I'm exhausted"
                elif energy < 0.25:
                    emotion_desc = emotion_desc + " — I can barely think"
            except Exception:
                pass
        reason = self._build_reason(emotional_state, primary_emotion, peer_utterance)
        plan = self._intend_action(intended_action, action_rationale, goal)
        utterance = self._compose_utterance(reason, plan, peer_utterance, recent_memory)

        # Coherence check and repair
        if not self._check_coherence(utterance, dialogue_history, peer_utterance):
            utterance = self._repair_utterance(utterance, dialogue_history, emotional_state, peer_utterance)

        # Update mention timer state
        if not suppressed and peer_utterance:
            self.last_peer_utterance = peer_utterance
            self._mention_timer = self.mention_cooldown
        elif self._mention_timer > 0:
            self._mention_timer -= 1

        return utterance

    def _describe_emotion(self, emotional_state: Dict[str, float], primary_emotion: str) -> str:
        valence = emotional_state.get("affect_valence", 0.5)
        arousal = emotional_state.get("affect_arousal", 0.5)
        if primary_emotion in {"fear", "anxious", "distressed", "afraid"}:
            return "I feel uneasy and tense"
        if primary_emotion in {"calm", "content"}:
            return "I feel calm and steady"
        if primary_emotion in {"motivated", "enthusiastic"}:
            return "I feel energized and focused"
        if primary_emotion in {"sad", "alienated"}:
            return "I feel low and cautious"
        if valence >= 0.60 and arousal > 0.55:
            return "I feel alert and curious"
        if valence < 0.45 and arousal > 0.55:
            return "I feel concerned and uneasy"
        return "I feel balanced"

    def _build_reason(
        self,
        emotional_state: Dict[str, float],
        primary_emotion: str,
        peer_utterance: Optional[str],
    ) -> str:
        valence = emotional_state.get("affect_valence", 0.5)
        arousal = emotional_state.get("affect_arousal", 0.5)
        confidence = emotional_state.get("confidence", 0.5)
        caution = emotional_state.get("caution", 0.5)

        if peer_utterance:
            return (
                f"I heard your words and I want to respond thoughtfully. "
                f"Your concern makes me reconsider how much risk I can accept right now."
            )

        if primary_emotion in {"fear", "anxious", "distressed", "afraid"}:
            return "I sense danger and I am trying to avoid a worse outcome."
        if primary_emotion in {"calm", "content"} and valence > 0.65:
            return "I am feeling stable enough to make a clear choice."
        if confidence < 0.45:
            return "I am uncertain, so I need to be careful before moving forward."
        if caution > 0.60:
            return "I feel cautious and prefer safer, smaller steps."
        if arousal > 0.60:
            return "I feel energized and ready to act with purpose."
        return "I am basing my choice on what seems most adaptive in this moment."

    def _intend_action(self, action: str, rationale: str, goal: str) -> str:
        return f"I intend to {action} because {rationale} toward {goal}."

    def _compose_utterance(
        self,
        reason: str,
        plan: str,
        peer_utterance: Optional[str],
        recent_memory: Optional[List[str]],
    ) -> str:
        # Prefer non-quoted references to avoid nested quoting and verbosity.
        if peer_utterance:
            # Keep peer quote short to avoid flooding the UI
            short_peer = peer_utterance.split('.')[0]
            if len(short_peer) > 120:
                short_peer = short_peer[:117].rsplit(' ', 1)[0] + '...'
            base = f"Regarding that, when you said '{short_peer}', {reason} {plan}"
        else:
            base = f"{reason} {plan}"

        if recent_memory:
            memory_snippet = ", then ".join(recent_memory[-2:])
            return f"{base} I remember that {memory_snippet}."
        return base

    def _sanitize_peer_utterance(self, peer: str) -> str:
        """Remove recursive "When you said" phrasing and excessive internal markers."""
        if not peer:
            return peer
        p = peer.strip()
        # Remove nested lead-ins like "When you said '... '" or repeated prefixes
        low = p.lower()
        if low.startswith("when you said"):
            # strip up to the first quote if present
            if "'" in p or '"' in p:
                # remove prefix and surrounding quotes
                p = p.split("'", 1)[-1] if "'" in p else p.split('"', 1)[-1]
                p = p.rstrip('"').rstrip("'")
            else:
                # remove the phrase
                p = p[len("when you said"):].strip(' :,-"\'')

        # Trim to reasonable length
        if len(p) > 400:
            p = p[:380].rsplit(' ', 1)[0] + '...'
        return p

    def _check_coherence(
        self,
        utterance: str,
        dialogue_history: List[str],
        peer_utterance: Optional[str],
    ) -> bool:
        if not dialogue_history:
            return True

        recent = " ".join(dialogue_history[-self.coherence_window:]).lower()
        utterance_lower = utterance.lower()

        if peer_utterance and "you" not in utterance_lower and "your" not in utterance_lower:
            return False

        if any(word in utterance_lower for word in ["because", "I feel", "I think", "I intend"]):
            return True

        if len(set(recent.split()) & set(utterance_lower.split())) > 2:
            return True

        return False

    def _repair_utterance(
        self,
        utterance: str,
        dialogue_history: List[str],
        emotional_state: Dict[str, float],
        peer_utterance: Optional[str],
    ) -> str:
        if peer_utterance:
            return (
                f"I need to correct that. I was too quick to decide without fully listening. "
                f"Because you raised that point, I will adjust and {utterance.lower()}"
            )

        return (
            f"I was wrong to say that so plainly. "
            f"I need to rethink this because my current state is not as simple as it seemed."
        )
