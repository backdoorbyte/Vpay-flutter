"""
Natural-language payment command parser for English, Hindi, and Hinglish.

Extracts recipient, amount (INR), and optional note from transcribed text.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

from models.schemas import ParsedCommand

logger = logging.getLogger("vpay")

# ─── Hindi / Hinglish / English number words ──────────────────────────────────
# Covers 0-20, tens, hundreds, thousands, lakhs / crores
_WORDS: dict[str, int] = {
    # 0-9
    "zero": 0, "shunya": 0, "suno": 0,
    "one": 1, "ek": 1, "एक": 1, "ik": 1,
    "two": 2, "do": 2, "दो": 2,
    "three": 3, "teen": 3, "तीन": 3,
    "four": 4, "char": 4, "chār": 4, "चार": 4,
    "five": 5, "paanch": 5, "panch": 5, "पाँच": 5,
    "six": 6, "chhe": 6, "che": 6, "छह": 6, "chhah": 6,
    "seven": 7, "saat": 7, "sāat": 7, "सात": 7,
    "eight": 8, "aath": 8, "āth": 8, "आठ": 8,
    "nine": 9, "nau": 9, "nauu": 9, "नौ": 9,
    # 10-19
    "ten": 10, "das": 10, "दस": 10,
    "eleven": 11, "gyarah": 11, "gyārah": 11, "ग्यारह": 11,
    "twelve": 12, "barah": 12, "bārah": 12, "बारह": 12,
    "thirteen": 13, "terah": 13, "terā": 13, "तेरह": 13,
    "fourteen": 14, "chaudah": 14, "chaudā": 14, "चौदह": 14,
    "fifteen": 15, "pandrah": 15, "pandrā": 15, "पंद्रह": 15,
    "sixteen": 16, "solah": 16, "solā": 16, "सोलह": 16,
    "seventeen": 17, "sattrah": 17, "sattrā": 17, "सत्रह": 17,
    "eighteen": 18, "atharah": 18, "athārā": 18, "अठारह": 18,
    "nineteen": 19, "unnees": 19, "unnīs": 19, "उन्नीस": 19,
    # 20-90
    "twenty": 20, "bees": 20, "बीस": 20,
    "thirty": 30, "tees": 30, "tīs": 30, "तीस": 30,
    "forty": 40, "chalis": 40, "chālīs": 40, "चालीस": 40,
    "fifty": 50, "pachas": 50, "pachās": 50, "पचास": 50,
    "sixty": 60, "sath": 60, "sāth": 60, "साठ": 60,
    "seventy": 70, "sattar": 70, "sattār": 70, "सत्तर": 70,
    "eighty": 80, "assi": 80, "assī": 80, "अस्सी": 80,
    "ninety": 90, "nabbe": 90, "nabbē": 90, "नब्बे": 90,
    # Multipliers
    "hundred": 100, "sau": 100, "soo": 100, "soy": 100, "soi": 100, "sui": 100, "सौ": 100,
    "thousand": 1000, "hazaar": 1000, "hazar": 1000, "hazār": 1000, "हज़ार": 1000,
    "lakh": 100000, "lac": 100000, "lākh": 100000, "लाख": 100000,
    "crore": 10000000, "crores": 10000000, "karod": 10000000, "karor": 10000000, "क्रोड़": 10000000,
}

# Words that multiply the preceding value (e.g. "do hazaar" = 2000)
MULTIPLIERS = {"hundred", "sau", "soo", "सौ",
               "thousand", "hazaar", "hazar", "hazār", "हज़ार",
               "lakh", "lac", "lākh", "लाख",
               "crore", "crores", "karod", "karor", "क्रोड़"}

# Devanagari digits → Arabic digits
_DEVANAGARI_DIGITS = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
    # Extended range
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
}


def _convert_devanagari_to_digits(text: str) -> str:
    """Convert Devanagari digits (१, २, ३, etc.) to Arabic numerals."""
    for hindi, arb in _DEVANAGARI_DIGITS.items():
        text = text.replace(hindi, arb)
    return text


def _normalize(text: str) -> str:
    """Lowercase, strip, collapse spaces, convert Devanagari digits."""
    text = text.strip().lower()
    text = _convert_devanagari_to_digits(text)
    return re.sub(r"\s+", " ", text)


def _tokenize(text: str) -> list[str]:
    """Split on whitespace/punctuation, keep only meaningful tokens."""
    return text.split()


def _parse_amount_from_words(text: str) -> Optional[float]:
    """
    Parse amount from a Hindi / Hinglish / English payment utterance.
    Handles digit sequences, Devanagari numerals, and word-based numbers.
    """
    normalized = _normalize(text)

    # 1. Check for digit sequences (highest confidence)
    # Collapse spaced digits first: "5 0 0" → "500"
    collapsed = re.sub(r"(\d)\s+(?=\d)", r"\1", normalized)
    digit_match = re.search(r"\b(\d+(?:,\d{2,3})*(?:\.\d+)?)\b", collapsed)
    if digit_match:
        val_str = digit_match.group(1).replace(",", "")
        # Avoid phone numbers (10+ digits)
        if len(val_str.replace(".", "")) < 10:
            logger.debug(f"Amount found via digit: {val_str}")
            return float(val_str)

    # 2. Currency-tagged amounts (e.g. "500 rupaye", "₹500")
    currency_match = re.search(
        r"(?:₹|rs\.?|rupees?|rupaye?|rupya|rupay|रुपये?|रु\.?)\s*(\d+(?:\.\d+)?)|"
        r"(\d+(?:\.\d+)?)\s*(?:rupees?|rupaye?|rs|₹|रुपये?|रु\.?)",
        collapsed,
        re.IGNORECASE,
    )
    if currency_match:
        val = currency_match.group(1) or currency_match.group(2)
        logger.debug(f"Amount found via currency tag: {val}")
        return float(val)

    # 3. Word-based amounts (Hindi/English composite numbers)
    # Remove common stop words that interfere with number parsing
    stop_words = {"bhejo", "bhejiye", "bhejna", "send", "pay", "transfer",
                  "bhej", "do", "de", "dena", "dein", "dijiye", "kar", "karo", "kariye"}

    tokens = collapsed.split()
    # Temporarily strip trailing stop words for cleaner parsing
    stripped_tokens = tokens[:]
    while stripped_tokens and stripped_tokens[-1] in stop_words:
        stripped_tokens.pop()

    amount = _parse_word_based_amount(stripped_tokens)
    if amount is not None and amount > 0:
        logger.debug(f"Amount found via word parsing: {amount}")
        return float(amount)

    # 4. Try again with original tokens
    amount = _parse_word_based_amount(tokens)
    if amount is not None and amount > 0:
        logger.debug(f"Amount found via word parsing (original): {amount}")
        return float(amount)

    return None


def _parse_word_based_amount(tokens: list[str]) -> Optional[int]:
    """
    Parse word-based numbers into an integer.
    Supports: 'ek' (1), 'pair' (20), 'teh' (30), 'pischo' (50),
              'sau' (100), 'hazaar' (1000), etc.
    Also supports composite: 'do hazaar pachas' → 2000 + 50 = 2050
    """
    # Words that indicate "do" is a verb, not a number
    verbs_before_do = {"bhej", "bhejo", "bhejiye", "bhejna", "de", "dein", "dena", "dijiye"}

    total = 0
    current_group = 0
    prev_token = None

    for token in tokens:
        if token not in _WORDS:
            prev_token = token
            continue

        # Skip "do" (2) when it follows a verb like "bhej do" (send/give)
        if token == "do" and prev_token in verbs_before_do:
            prev_token = token
            continue

        val = _WORDS[token]

        if token in MULTIPLIERS:
            # Multiplier: "hazaar", "sau", "lakh", etc.
            if current_group == 0:
                current_group = 1
            total += current_group * val
            current_group = 0
        else:
            # Simple number
            current_group += val

        prev_token = token

    total += current_group
    return total if total > 0 else None


def _extract_recipient(text: str, amount: Optional[float]) -> Optional[str]:
    """
    Heuristics for recipient names in EN/HI/Hinglish commands.
    """
    # Pre-process text to remove common punctuation that might break regex
    clean_text = re.sub(r"[.!?]", "", text).strip()

    patterns = [
        # "Send 500 rupees to Rahul"
        r"(?:send|transfer|pay|bhej(?:o|iye|na)?|भेज(?:ो|िए)?|दो|do)\s+.*?\s+to\s+([A-Za-zऀ-ॿ]+)",
        r"\bto\s+([A-Za-zऀ-ॿ]+)",
        # "Rahul ko 500" / "Rahul ko bhejo"
        r"([A-Za-zऀ-ॿ]+)\s+ko\b",
        # "Pay Rahul 500"
        r"(?:send|transfer|pay|bhej(?:o|iye|na)?|भेज(?:ो|िए)?|दो|do)\s+([A-Za-zऀ-ॿ]+)\s+",
        # "राहुल को"
        r"([ऀ-ॿ]+)\s*को\b",
    ]

    for pat in patterns:
        m = re.search(pat, clean_text, re.IGNORECASE)
        if m:
            name = m.group(1).strip().title()
            # Filter out common false positives
            if name.lower() not in {"rs", "rupees", "rupaye", "send", "bhejo", "rupya", "rupay", "amount", "payment"}:
                return name

    # 10-digit mobile or hyphenated STT number as payee
    m = re.search(r"\b(\d{10})\b", clean_text)
    if m:
        return m.group(1)

    # Fallback: if we have an amount, any word that isn't the amount or a stopword could be the name
    if amount is not None:
        words = clean_text.split()
        stop_words = {"send", "pay", "to", "ko", "bhejo", "transfer", "rupees", "rs", "rupaye", "for", "please"}
        for w in words:
            w_clean = w.strip().title()
            if w.lower() not in stop_words and not re.search(r"\d", w):
                if len(w) >= 3:
                    return w_clean

    return None


def _extract_note(text: str) -> Optional[str]:
    for pat in [
        r"(?:for|note|purpose|regarding|ke liye)\s+(.+)$",
        r"(?:liye|के लिए)\s+(.+)$",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()[:200]
    return None


def parse_payment_command(text: str) -> ParsedCommand:
    """
    Parse transcribed speech into structured payment fields.

    Supports amounts in:
      - Digits: "500", "5,000", "1.5"
      - Hindi words: "do hazaar", "panch sau", "teen hazaar ek sau"
      - Hinglish: "500 rupaye", "paanch sau"
      - Devanagari: "राहुल को ५०० रुपये भेजो"

    Examples:
        - "Send 500 rupees to Rahul"
        - "Rahul ko 500 rupaye bhejo"
        - "राहुल को 500 रुपये भेजो"
        - "Priya ko do hazaar rupaye do"
        - "2000 rupaye bhej do"
    """
    raw = text.strip()

    amount = _parse_amount_from_words(raw)
    recipient = _extract_recipient(raw, amount)
    note = _extract_note(raw)

    confidence = 0.0
    if amount is not None:
        confidence += 0.4
    if recipient is not None:
        confidence += 0.3

    return ParsedCommand(
        recipient=recipient,
        amount=amount,
        note=note,
        raw_text=raw,
        confidence=confidence,
        resolution="unknown",
    )
