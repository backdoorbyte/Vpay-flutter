"""
POST /voice-pay — transcribe + parse + resolve UPI in one step.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

import aiosqlite
from config import MAX_AUDIO_SECONDS_PAY, PARSE_MIN_CONFIDENCE
from database.connection import get_db
from services.display_formatter import format_confirm_prompt, format_payment_display
from models.schemas import VoicePayResponse
from services.recipient_resolver import (
    isolate_latest_command,
    parse_and_resolve_text,
    resolve_recipient,
)
from services.whisper_service import transcribe_audio
from utils.audio import cleanup_path, save_upload_to_wav

router = APIRouter(tags=["Voice Pay"])

logger = logging.getLogger("vpay")

DEFAULT_USER_ID = 1


def _finalize_confidence(parsed):
    """Boost confidence when UPI is resolved."""
    if parsed.amount is not None and parsed.upi_id:
        return max(parsed.confidence, 0.85)
    if parsed.upi_id:
        return max(parsed.confidence, 0.55)
    if parsed.amount is not None and parsed.recipient:
        return max(parsed.confidence, 0.55)
    return parsed.confidence


@router.post("/voice-pay/parse", response_model=VoicePayResponse)
async def voice_pay_parse(
    audio: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Record payment command → STT → parse → resolve contact / spoken UPI."""
    wav_path: Path | None = None
    try:
        wav_path = await save_upload_to_wav(audio, max_seconds=MAX_AUDIO_SECONDS_PAY)
        text, detected = await asyncio.to_thread(
            transcribe_audio, wav_path, None  # Auto-detect language (works for Hinglish)
        )
        logger.info(f"Transcribed Text: '{text}' (Language: {detected})")
        
        command = isolate_latest_command(text)
        logger.info(f"Isolated Command: '{command}'")
        
        parsed = parse_and_resolve_text(text)
        parsed = await resolve_recipient(db, text, parsed, DEFAULT_USER_ID)
        parsed = parsed.model_copy(update={"confidence": _finalize_confidence(parsed)})
        
        logger.info(f"Parsed Result: {parsed.model_dump()}")

        display_text = command
        confirm_prompt = ""
        if parsed.amount is not None and parsed.upi_id:
            display_text = format_payment_display(parsed.amount, parsed.upi_id)
            confirm_prompt = format_confirm_prompt(parsed.upi_id, parsed.amount)

        return VoicePayResponse(
            transcribed_text=command,
            display_text=display_text,
            confirm_prompt=confirm_prompt,
            language=detected,
            parsed=parsed,
            needs_upi=bool(parsed.amount and not parsed.upi_id),
        )
    finally:
        if wav_path:
            cleanup_path(wav_path)
