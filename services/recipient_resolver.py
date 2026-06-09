"""Resolve parsed voice commands to a concrete UPI ID."""

from __future__ import annotations

import re

import aiosqlite

from models.schemas import ParsedCommand
from services import contact_service
from services.upi_normalizer import (
    extract_upi_from_speech,
    isolate_latest_command,
    strip_upi_from_text,
)

from services.display_formatter import infer_amount_from_pay_command
from services.upi_utils import is_valid_upi, normalize_upi


async def resolve_recipient(
    db: aiosqlite.Connection,
    text: str,
    parsed: ParsedCommand,
    user_id: int = 1,
) -> ParsedCommand:
    """
    Enrich parsed command with upi_id via spoken UPI, contact name, or phone.
    """
    upi_id = parsed.upi_id or extract_upi_from_speech(isolate_latest_command(text))
    resolution = parsed.resolution

    if upi_id and is_valid_upi(upi_id):
        upi_id = normalize_upi(upi_id)
        contact = await contact_service.find_by_upi(db, upi_id, user_id)
        display = contact["name"] if contact else _display_from_upi(upi_id)
        resolution = "spoken_upi"
        confidence = parsed.confidence
        if parsed.amount is not None:
            confidence = min(1.0, confidence + 0.2)
        return parsed.model_copy(
            update={
                "upi_id": upi_id,
                "recipient": display,
                "resolution": resolution,
                "confidence": confidence,
            }
        )

    if parsed.recipient:
        contact = await contact_service.find_by_name(db, parsed.recipient, user_id)
        if contact:
            return parsed.model_copy(
                update={
                    "recipient": contact["name"],
                    "upi_id": contact["upi_id"],
                    "resolution": "contact",
                    "confidence": min(1.0, parsed.confidence + 0.2),
                }
            )

        digits = re.sub(r"\D", "", parsed.recipient)
        if len(digits) == 10:
            contact = await contact_service.find_by_phone(db, digits, user_id)
            if contact:
                return parsed.model_copy(
                    update={
                        "recipient": contact["name"],
                        "upi_id": contact["upi_id"],
                        "resolution": "contact_phone",
                        "confidence": min(1.0, parsed.confidence + 0.2),
                    }
                )
            return parsed.model_copy(
                update={
                    "upi_id": f"{digits}@ybl",
                    "recipient": digits,
                    "resolution": "spoken_phone",
                    "confidence": min(1.0, parsed.confidence + 0.15),
                }
            )

    return parsed.model_copy(update={"resolution": resolution or "unresolved"})


def _display_from_upi(upi_id: str) -> str:
    handle = upi_id.split("@", 1)[0]
    if handle.isdigit() and len(handle) == 10:
        return handle
    return handle.replace(".", " ").title()


def parse_and_resolve_text(text: str) -> ParsedCommand:
    """Parse command with UPI stripped from text first (sync step before DB resolve)."""
    from services.command_parser import parse_payment_command

    command = isolate_latest_command(text)
    upi_id = extract_upi_from_speech(command)
    cleaned = strip_upi_from_text(command, upi_id)
    parsed = parse_payment_command(cleaned if cleaned else command)
    parsed = parsed.model_copy(update={"raw_text": command})
    if upi_id:
        upi_id = normalize_upi(upi_id)
        parsed = parsed.model_copy(
            update={
                "upi_id": upi_id,
                "resolution": "spoken_upi",
            }
        )
    if parsed.amount is None and upi_id:
        inferred = infer_amount_from_pay_command(command, upi_id)
        if inferred is not None:
            parsed = parsed.model_copy(
                update={
                    "amount": inferred,
                    "confidence": min(1.0, parsed.confidence + 0.3),
                }
            )
    return parsed
