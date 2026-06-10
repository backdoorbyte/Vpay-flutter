"""
POST /parse — extract payment fields from transcribed text.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from config import PARSE_MIN_CONFIDENCE
from models.schemas import ParsedCommand, ParseRequest
from services.command_parser import parse_payment_command

router = APIRouter(tags=["Command Parsing"])


@router.post("/", response_model=ParsedCommand)
async def parse_command(body: ParseRequest):
    """Parse recipient, amount, and note from natural language."""
    result = parse_payment_command(body.text)
    if result.confidence < PARSE_MIN_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Could not confidently parse payment command",
                "parsed": result.model_dump(),
                "min_confidence": PARSE_MIN_CONFIDENCE,
            },
        )
    return result
