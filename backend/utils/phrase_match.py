"""
Fuzzy phrase matching for challenge-response (STT may drop words or add noise).
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _tokenize(text: str) -> list[str]:
    text = re.sub(r"[^\w\s\u0900-\u097F]", " ", text.lower())
    return [t for t in text.split() if len(t) > 1]


def phrase_match_score(expected: str, spoken_text: str) -> float:
    """
    Compare expected challenge phrase to transcribed speech.

    Uses token overlap + sequence ratio; returns 0.0–1.0.
    """
    exp_tokens = _tokenize(expected)
    spk_tokens = _tokenize(spoken_text)
    if not exp_tokens:
        return 0.0

    # Nonce at end of challenge — must appear in speech
    nonce = exp_tokens[-1] if exp_tokens[-1].isdigit() else None
    if nonce and nonce not in spoken_text and nonce not in " ".join(spk_tokens):
        return 0.0

    overlap = sum(1 for t in exp_tokens if t in spk_tokens) / len(exp_tokens)
    ratio = SequenceMatcher(
        None, " ".join(exp_tokens), " ".join(spk_tokens)
    ).ratio()
    return max(overlap, ratio) * 0.5 + min(overlap, ratio) * 0.5


def phrase_matches(expected: str, spoken_text: str, min_ratio: float) -> tuple[bool, float]:
    score = phrase_match_score(expected, spoken_text)
    return score >= min_ratio, score
