"""
Extract UPI IDs from transcribed speech.

Supports:
  - rahul@ybl / 9876543210@ybl (literal)
  - "at the rate ybl" (Indian English for @)
  - hyphenated STT numbers: 914-247-8891
  - spoken digit sequences (not prepositions like "to")
"""

from __future__ import annotations

import re
from typing import Optional

from services.upi_utils import UPI_ID_PATTERN, is_valid_upi, normalize_upi

PSP_ALIASES: dict[str, str] = {
    "ybl": "ybl",
    "y b l": "ybl",
    "why b l": "ybl",
    "why bl": "ybl",
    "phonepe": "ybl",
    "phone pe": "ybl",
    "phone pay": "ybl",
    "paytm": "paytm",
    "pay tm": "paytm",
    "gpay": "okaxis",
    "g pay": "okaxis",
    "google pay": "okaxis",
    "googlepay": "okaxis",
    "okaxis": "okaxis",
    "ok axis": "okaxis",
    "okhdfcbank": "okhdfcbank",
    "hdfc": "okhdfcbank",
    "icici": "icici",
    "ibl": "ibl",
    "axl": "axl",
    "axis pay": "axl",
}

# Only unambiguous spoken digits — NOT "to", "for", "at" (prepositions)
DIGIT_WORDS: dict[str, str] = {
    "zero": "0",
    "oh": "0",
    "shunya": "0",
    "sifr": "0",
    "one": "1",
    "won": "1",
    "ek": "1",
    "two": "2",
    "too": "2",
    "three": "3",
    "teen": "3",
    "four": "4",
    "char": "4",
    "five": "5",
    "paanch": "5",
    "panch": "5",
    "six": "6",
    "chhe": "6",
    "che": "6",
    "seven": "7",
    "saat": "7",
    "eight": "8",
    "aath": "8",
    "ate": "8",
    "nine": "9",
    "nau": "9",
}

SKIP_TOKENS = {
    "to",
    "for",
    "at",
    "the",
    "rate",
    "of",
    "pay",
    "send",
    "transfer",
    "rupees",
    "rupaye",
    "rupya",
    "rs",
    "bhejo",
    "bhejiye",
}


def preprocess_speech(text: str) -> str:
    """Normalize STT quirks before UPI extraction."""
    t = text.lower().strip()
    # Common whisper mishearing: "red" → "rate"
    t = re.sub(r"\bat the red\b", "at the rate", t)
    t = re.sub(r"\s+at the rate of\s+", "@", t)
    t = re.sub(r"\s+at the rate\s+", "@", t)
    for key in sorted(PSP_ALIASES.keys(), key=len, reverse=True):
        t = re.sub(rf"\s+at\s+{re.escape(key)}\b", f"@{PSP_ALIASES[key]}", t)
    t = re.sub(r"\s+@\s+", "@", t)
    return re.sub(r"\s+", " ", t).strip()


def isolate_latest_command(text: str) -> str:
    """Use the last payment-like sentence when STT returns multiple commands."""
    text = text.strip()
    if not text:
        return text
    parts = re.split(r"[.!?]+\s*", text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 1:
        return text
    pay_kw = (
        "pay",
        "send",
        "transfer",
        "bhejo",
        "bhej",
        "भेज",
        "@",
        "at the rate",
        "at ybl",
        "at paytm",
        "at phonepe",
    )
    for part in reversed(parts):
        lower = part.lower()
        if any(k in lower for k in pay_kw):
            return part
    return parts[-1]


def _normalize_psp_token(token: str) -> Optional[str]:
    key = re.sub(r"\s+", " ", token.strip().lower())
    if key in SKIP_TOKENS:
        return None
    if key in PSP_ALIASES:
        return PSP_ALIASES[key]
    collapsed = key.replace(" ", "")
    return PSP_ALIASES.get(collapsed, collapsed if collapsed.isalnum() else None)


def _normalize_psp_from_segment(segment: str) -> Optional[str]:
    segment = re.sub(r"\s+", " ", segment.strip().lower())
    for key in sorted(PSP_ALIASES.keys(), key=len, reverse=True):
        if segment == key or segment.startswith(key + " "):
            return PSP_ALIASES[key]
    first = segment.split()[0] if segment.split() else segment
    if first in SKIP_TOKENS:
        return None
    return _normalize_psp_token(first)


def _token_to_digit(token: str) -> Optional[str]:
    t = token.strip(".,;").lower()
    if t in SKIP_TOKENS:
        return None
    if t.isdigit():
        return t
    return DIGIT_WORDS.get(t)


def _find_indian_mobile(digits: str) -> Optional[str]:
    """Find a 10-digit Indian mobile (starts 6–9) inside a digit run."""
    if len(digits) == 10 and digits[0] in "6789":
        return digits
    for i in range(len(digits) - 9):
        chunk = digits[i : i + 10]
        if chunk[0] in "6789":
            return chunk
    if len(digits) >= 10:
        tail = digits[-10:]
        if tail[0] in "6789":
            return tail
    return None


def _phone_from_segment(segment: str) -> Optional[str]:
    """Extract 10-digit mobile from segment (handles hyphenated STT output)."""
    segment = segment.lower().strip()
    if " to " in segment:
        segment = segment.rsplit(" to ", 1)[-1].strip()

    for m in re.finditer(r"\d(?:[\d-]*\d)", segment):
        digits = re.sub(r"\D", "", m.group())
        phone = _find_indian_mobile(digits)
        if phone:
            return phone

    tokens = segment.split()
    spoken: list[str] = []
    for tok in tokens:
        d = _token_to_digit(tok)
        if d is not None:
            spoken.append(d)
    if spoken:
        phone = _find_indian_mobile("".join(spoken))
        if phone:
            return phone

    trailing: list[str] = []
    for tok in reversed(tokens):
        d = _token_to_digit(tok)
        if d is None:
            break
        trailing.insert(0, d)
    if trailing:
        return _find_indian_mobile("".join(trailing))
    return None


def _normalize_matched_upi(raw: str) -> Optional[str]:
    if "@" not in raw:
        return None
    handle, psp = raw.split("@", 1)
    handle = handle.strip().lower()
    psp = psp.strip().lower()
    if re.fullmatch(r"[\d-]+", handle):
        digits = re.sub(r"\D", "", handle)
        phone = _find_indian_mobile(digits)
        if not phone:
            return None
        handle = phone
    if handle in DIGIT_WORDS or handle in SKIP_TOKENS:
        return None
    candidate = f"{handle}@{psp}"
    if is_valid_upi(candidate):
        return normalize_upi(candidate)
    return None


def _extract_literal_upi(text: str) -> Optional[str]:
    preprocessed = preprocess_speech(text)
    for token in re.split(r"[\s,;]+", preprocessed):
        cleaned = token.strip(".,;\"'")
        if "@" in cleaned:
            upi = _normalize_matched_upi(cleaned)
            if upi:
                return upi
    compact = re.sub(r"\s+", "", preprocessed)
    m = re.search(r"([\w.-]+@[\w.-]+)", compact)
    if m:
        return _normalize_matched_upi(m.group(1))
    return None


def _handle_from_segment(segment: str) -> Optional[str]:
    """Parse alphabetic payee handle (e.g. rahul dot sharma)."""
    phone = _phone_from_segment(segment)
    if phone:
        return phone

    segment = segment.lower().strip()
    segment = re.sub(r"\bdot\b|\bpoint\b", ".", segment)
    segment = re.sub(r"\s+", " ", segment)
    if " to " in segment:
        segment = segment.rsplit(" to ", 1)[-1].strip()

    handle_tokens: list[str] = []
    for tok in segment.split():
        clean = tok.strip(".,;")
        if clean in SKIP_TOKENS or clean.isdigit() or clean in DIGIT_WORDS:
            continue
        if re.fullmatch(r"[\d-]+", clean):
            continue
        handle_tokens.append(clean)

    if not handle_tokens:
        return None
    handle = "".join(handle_tokens)
    handle = re.sub(r"\.+", ".", handle)
    return handle if handle else None


def _extract_spoken_upi(text: str) -> Optional[str]:
    normalized = preprocess_speech(text)

    if "@" not in normalized:
        return None

    left, right = normalized.rsplit("@", 1)
    psp = _normalize_psp_from_segment(right.strip())
    if not psp:
        return None

    handle = _phone_from_segment(left) or _handle_from_segment(left)
    if not handle:
        return None

    candidate = f"{handle}@{psp}"
    if is_valid_upi(candidate):
        return normalize_upi(candidate)
    return None


def extract_upi_from_speech(text: str) -> Optional[str]:
    """Return normalized UPI ID if found in transcribed speech."""
    if not text or not text.strip():
        return None
    command = isolate_latest_command(text)
    spoken = _extract_spoken_upi(command)
    if spoken:
        return spoken
    return _extract_literal_upi(command)


def strip_upi_from_text(text: str, upi_id: Optional[str]) -> str:
    """Remove UPI-related tokens so amount/name parsing is not confused."""
    if not upi_id:
        return text
    result = preprocess_speech(text)
    handle, psp = upi_id.split("@", 1)
    for pat in [
        re.escape(upi_id),
        rf"{re.escape(handle)}\s*@\s*{re.escape(psp)}",
        rf"{re.escape(handle)}\s+at the rate\s+{re.escape(psp)}",
        rf"{re.escape(handle)}\s+at\s+{re.escape(psp)}",
    ]:
        result = re.sub(pat, " ", result, flags=re.IGNORECASE)
    if handle.isdigit() and len(handle) == 10:
        result = re.sub(rf"\b{handle}\b", " ", result)
    return re.sub(r"\s+", " ", result).strip()
