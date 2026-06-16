"""Shared UPI ID validation helpers."""

from __future__ import annotations

import re

# Handles: username@psp or 10-digit phone@psp
UPI_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$")
PHONE_UPI_PATTERN = re.compile(r"^\d{10}@[a-zA-Z0-9]+$")


def is_valid_upi(upi_id: str) -> bool:
    return bool(UPI_ID_PATTERN.match(upi_id.strip()))


def normalize_upi(upi_id: str) -> str:
    return upi_id.strip().lower()
