"""Human-readable payment command and TTS prompt formatting."""

from __future__ import annotations

import re
from typing import Optional


def format_payment_display(amount: float, upi_id: str) -> str:
    """e.g. Pay 200 to 9142478894@ybl"""
    amt = int(amount) if amount == int(amount) else amount
    return f"Pay {amt} to {upi_id}"


def format_confirm_prompt(upi_id: str, amount: Optional[float] = None, language: str = "en") -> str:
    """Spoken by the voice agent before user confirms."""
    if amount is not None:
        amt = int(amount) if amount == int(amount) else amount
        if language == "hi":
            return f"{amt} rupaye {upi_id} bhejne ke liye, haan bol kar payment ki pushti karein"
        return f"Confirm the payment of {amt} rupees to {upi_id}"
    if language == "hi":
        return f"{upi_id} ko payment bhejne ke liye, haan bol kar pushti karein"
    return f"Confirm the payment to {upi_id}"


def infer_amount_from_pay_command(command: str, upi_id: str) -> Optional[float]:
    """
    Extract amount when STT merges amount and phone: "Pay 200-914-2478894 at the rate YBL".
    """
    if not command or not upi_id:
        return None
    lower = command.lower().strip()
    phone = upi_id.split("@", 1)[0]

    m = re.search(
        r"(?:pay|send|transfer|bhej(?:o|iye|na)?)\s+(\d+(?:\.\d+)?)\s*[-\s]",
        lower,
    )
    if m:
        return float(m.group(1))

    m = re.search(
        rf"(\d+(?:\.\d+)?)\s*[-\s]+{re.escape(phone[:4])}",
        lower,
    )
    if m:
        return float(m.group(1))

    m = re.search(
        r"(?:₹|rs\.?|rupees?|rupaye?|rupya)\s*(\d+(?:\.\d+)?)",
        lower,
    )
    if m:
        return float(m.group(1))

    return None
