"""Detect yes / confirm phrases for voice payment confirmation (EN / HI / Hinglish)."""

from __future__ import annotations

import re

CONFIRM_PATTERNS = [
    # English
    r"\byes\b.*\bconfirm",
    r"\bconfirm\b.*\bpayment",
    r"\byes\b.*\bpayment",
    r"\bi confirm\b",
    r"\bconfirmed\b",
    r"\bgo ahead\b",
    r"\bproceed\b",
    r"\bapprove\b",
    r"\byes\b.*\bcorrect\b",      # e.g. "yes, that's correct"
    r"\byeah\b.*\bconfirm",       # e.g. "yeah, confirm it"
    r"\bdone\b",                  # short affirmative
    # Hindi / Devanagari
    r"हाँ.*(पुष्टि|कन्फर्म|भुगतान)",
    r"(पुष्टि|कन्फर्म).*(कर|करो|करें|की)",
    r"भुगतान.*(पुष्टि|कन्फर्म|कर)",
    r"ठीक\s*है",
    r"हाँ\s*कर\s*दो",
    # Hinglish / Roman Hindi
    r"\bhaan\b.*\bconfirm",
    r"\bhaan\b.*\bpayment",
    r"\bhaan\b.*\bkar\s*do",
    r"\btheek\s*hai\b",
    r"\bsahi\s*hai\b",
    r"\bconfirm\s*kar\s*do",
    r"\bpayment\s*confirm",
    r"\bji\s*haan\b",
    r"\byes\s*confirm",
    r"\bok\s*confirm",
]

NEGATION_PATTERNS = [
    r"\bno\b.*\bconfirm",
    r"\bcancel\b",
    r"\bmat\b.*\bkar",
    r"\bstop\b",
    r"रद्द",
    r"नहीं",
    r"\bnahi\b",
]


def is_payment_confirmation(text: str) -> tuple[bool, float]:
    """
    Return (is_confirm, confidence 0-1) for transcribed confirmation speech.
    """
    if not text or not text.strip():
        return False, 0.0

    normalized = re.sub(r"\s+", " ", text.strip().lower())

    for pat in NEGATION_PATTERNS:
        if re.search(pat, normalized, re.IGNORECASE):
            return False, 0.0

    for pat in CONFIRM_PATTERNS:
        if re.search(pat, normalized, re.IGNORECASE):
            return True, 0.9

    # Short affirmatives
    short_yes = {
        "yes",
        "yeah",
        "yep",
        "confirm",
        "confirmed",
        "haan",
        "ha",
        "ji",
        "ok",
        "okay",
        "theek hai",
        "sahi hai",
        "कर दो",
        "हाँ",
        "जी हाँ",
    }
    # Strip trailing punctuation before exact comparison
    clean = normalized.rstrip(".,;!?")
    if clean in short_yes:
        return True, 0.75

    # More lenient: any word starting with "confirm" paired with an affirmative cue
    if "confirm" in normalized and any(
        w in normalized for w in ("yes", "haan", "ha", "ji", "payment", "pay", "theek", "sahi")
    ):
        return True, 0.85

    return False, 0.0
