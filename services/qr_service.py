"""
Decode payment QR images and extract UPI payee details.
"""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import parse_qs, unquote, urlparse

import cv2
import numpy as np

from services.upi_utils import UPI_ID_PATTERN


def decode_qr_from_bytes(image_bytes: bytes) -> str:
    """Read QR payload string from an uploaded image."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not read image. Use PNG or JPEG.")

    detector = cv2.QRCodeDetector()
    payload, _, _ = detector.detectAndDecode(image)
    if not payload or not payload.strip():
        raise ValueError("No QR code found in this image.")

    return payload.strip()


def _first_param(params: dict[str, list[str]], key: str) -> Optional[str]:
    values = params.get(key)
    if not values or not values[0]:
        return None
    return unquote(values[0]).strip()


def parse_upi_payload(payload: str) -> dict[str, Any]:
    """
    Parse UPI QR payloads (upi://pay?pa=...) or plain UPI IDs.
    """
    raw = payload.strip()
    upi_id: Optional[str] = None
    payee_name: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None

    lower = raw.lower()
    if lower.startswith("upi:"):
        parsed = urlparse(raw)
        params = parse_qs(parsed.query)
        upi_id = _first_param(params, "pa")
        payee_name = _first_param(params, "pn")
        note = _first_param(params, "tn") or _first_param(params, "note")
        amount_str = _first_param(params, "am") or _first_param(params, "amount")
        if amount_str:
            try:
                amount = float(amount_str)
            except ValueError:
                amount = None
    elif "pa=" in lower:
        query = raw.split("?", 1)[-1] if "?" in raw else raw
        return parse_upi_payload(f"upi://pay?{query}")
    elif UPI_ID_PATTERN.match(raw):
        upi_id = raw
    elif "@" in raw:
        # Fallback: extract first token that looks like UPI ID
        for token in re.split(r"[\s,;]+", raw):
            if UPI_ID_PATTERN.match(token):
                upi_id = token
                break

    if not upi_id:
        raise ValueError("QR code does not contain a valid UPI ID.")

    return {
        "upi_id": upi_id,
        "payee_name": payee_name,
        "amount": amount,
        "note": note,
        "raw_payload": raw,
    }


def parse_qr_image(image_bytes: bytes) -> dict[str, Any]:
    payload = decode_qr_from_bytes(image_bytes)
    return parse_upi_payload(payload)
