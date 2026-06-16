"""
Payment intent + voice confirmation (replaces random challenge phrase for pay flow).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Union

import aiosqlite
import asyncpg
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from config import (
    CHALLENGE_TTL_SECONDS,
    MAX_AUDIO_SECONDS_CONFIRM,
    VERIFY_THRESHOLD,
)
from database.connection import get_db
from models.schemas import (
    ConfirmVerifyResponse,
    PaymentIntentRequest,
    PaymentIntentResponse,
)
from services import enrollment_service, payment_service
from services.confirm_parser import is_payment_confirmation
from services.display_formatter import format_confirm_prompt, format_payment_display
from services.speaker_service import get_threshold, verify_against_enrolled
from services.upi_utils import is_valid_upi
from services.whisper_service import transcribe_audio
from utils.audio import cleanup_path, save_upload_to_wav

router = APIRouter(tags=["Payment Intent"])
logger = logging.getLogger("vpay")

DEFAULT_USER_ID = 1

_intents: dict[int, dict] = {}
_verified_intents: dict[int, float] = {}
_next_intent_id = 1


def _new_intent_id() -> int:
    global _next_intent_id
    iid = _next_intent_id
    _next_intent_id += 1
    return iid


@router.post("", response_model=PaymentIntentResponse)
async def create_payment_intent(body: PaymentIntentRequest):
    """Register a pending payment and return TTS confirmation prompt."""
    if not is_valid_upi(body.upi_id):
        raise HTTPException(status_code=400, detail="Invalid UPI ID")

    intent_id = _new_intent_id()
    lang = body.language or "en"
    display = body.display_text or format_payment_display(body.amount, body.upi_id.lower())
    prompt = body.confirm_prompt or format_confirm_prompt(body.upi_id.lower(), body.amount, language=lang)

    _intents[intent_id] = {
        "user_id": DEFAULT_USER_ID,
        "recipient": body.recipient,
        "upi_id": body.upi_id.lower(),
        "amount": body.amount,
        "note": body.note,
        "display_text": display,
        "confirm_prompt": prompt,
        "language": lang,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=CHALLENGE_TTL_SECONDS),
        "used": False,
    }

    return PaymentIntentResponse(
        intent_id=intent_id,
        display_text=display,
        confirm_prompt=prompt,
        expires_in_seconds=CHALLENGE_TTL_SECONDS,
        language=lang,
    )


async def _verify_audio_async(
    wav_path: Path, enrolled, language: str = None
) -> tuple[str, bool, bool, float, np.ndarray]:
    (text, _), (speaker_ok, score, probe_emb) = await asyncio.gather(
        asyncio.to_thread(transcribe_audio, wav_path, language, fast=True),
        asyncio.to_thread(verify_against_enrolled, wav_path, enrolled, return_embedding=True),
    )
    confirm_ok, _ = is_payment_confirmation(text)
    return text, confirm_ok, speaker_ok, score, probe_emb


@router.post("/confirm", response_model=ConfirmVerifyResponse)
async def verify_payment_confirmation(
    intent_id: int = Query(...),
    audio: UploadFile = File(...),
    db: Union[aiosqlite.Connection, asyncpg.Pool] = Depends(get_db),
):
    """Verify voice confirm + complete payment in one request when successful."""
    intent = _intents.get(intent_id)
    if not intent:
        return ConfirmVerifyResponse(
            verified=False,
            score=0.0,
            threshold=get_threshold(),
            transcribed_text="",
            message="Payment session not found",
            response_text="Payment declined",
            language="en",
        )

    lang = intent.get("language", "en")
    if intent["used"]:
        return ConfirmVerifyResponse(
            verified=False,
            score=0.0,
            threshold=get_threshold(),
            transcribed_text="",
            message="Payment session already used",
            response_text="Payment declined",
            language=lang,
        )

    if datetime.now(timezone.utc) > intent["expires_at"]:
        return ConfirmVerifyResponse(
            verified=False,
            score=0.0,
            threshold=get_threshold(),
            transcribed_text="",
            message="Payment session expired",
            response_text="Payment declined",
            language=lang,
        )

    enrolled = await enrollment_service.get_enrolled_embedding(db, DEFAULT_USER_ID)
    if enrolled is None:
        return ConfirmVerifyResponse(
            verified=False,
            score=0.0,
            threshold=get_threshold(),
            transcribed_text="",
            message="Complete voice enrollment first",
            response_text="Payment declined",
            language=lang,
        )

    wav_path: Path | None = None
    try:
        wav_path = await save_upload_to_wav(
            audio, max_seconds=MAX_AUDIO_SECONDS_CONFIRM
        )
        text, confirm_ok, speaker_ok, score, probe_emb = await _verify_audio_async(
            wav_path, enrolled, None  # Auto-detect language (works for Hinglish)
        )
        logger.info(
            "[CONFIRM] transcript='%s' confirm_ok=%s speaker_ok=%s score=%.4f",
            text, confirm_ok, speaker_ok, score
        )
        verified = confirm_ok and speaker_ok and score >= VERIFY_THRESHOLD

        if not verified:
            reason = "confirm_phrase" if not confirm_ok else "speaker"
            logger.info("[CONFIRM FAIL] reason=%s confirm_ok=%s speaker_ok=%s score=%.4f", reason, confirm_ok, speaker_ok, score)
            msg_parts = []
            if not confirm_ok:
                msg_parts.append('Say "yes, confirm the payment"')
            if not speaker_ok:
                msg_parts.append("Speaker not recognized")
            return ConfirmVerifyResponse(
                verified=False,
                score=round(score, 4),
                threshold=get_threshold(),
                limit=0.0,
                transcribed_text=text,
                message="; ".join(msg_parts) or "Confirmation failed",
                response_text="Payment declined",
                language=intent.get("language", "en"),
            )

        # Refine embedding
        refined = await enrollment_service.refine_embedding(db, DEFAULT_USER_ID, probe_emb, score)

        mark_intent_used(intent_id)
        success, msg, new_balance, tx_id = await payment_service.process_payment(
            db,
            DEFAULT_USER_ID,
            intent["recipient"],
            intent["upi_id"],
            intent["amount"],
            intent["note"],
            score,
        )
        logger.info("[PAYMENT] success=%s msg=%s new_balance=%s tx_id=%s", success, msg, new_balance, tx_id)
        if not success:
            logger.info("[CONFIRM FAIL] reason=process_payment_failed msg=%s", msg)
            return ConfirmVerifyResponse(
                verified=False,
                score=round(score, 4),
                threshold=get_threshold(),
                limit=0.0,
                transcribed_text=text,
                message=msg,
                response_text="Payment declined",
                language=lang,
            )

        response = ConfirmVerifyResponse(
            verified=True,
            score=round(score, 4),
            threshold=get_threshold(),
            limit=0.0,
            refined=refined,
            transcribed_text=text,
            message=f"Payment confirmed (Confidence: {round(score*100)}%)",
            payment_completed=True,
            new_balance=new_balance,
            transaction_id=tx_id,
            response_text="Payment confirmed",
            language=intent.get("language", "en"),
        )
        logger.info(f"Returning confirmation response: verified={response.verified}, payment_completed={response.payment_completed}")
        return response
    except Exception as e:
        logger.error("[CONFIRM FAIL] reason=exception error=%s", str(e))
        return ConfirmVerifyResponse(
            verified=False,
            score=0.0,
            threshold=get_threshold(),
            transcribed_text="",
            message=str(e),
            response_text="Payment declined",
            language=lang,
        )
    finally:
        if wav_path:
            cleanup_path(wav_path)


def is_intent_verified(intent_id: int) -> bool:
    return intent_id in _verified_intents


def pop_verified_score(intent_id: int) -> float | None:
    return _verified_intents.pop(intent_id, None)


def get_intent(intent_id: int) -> dict | None:
    return _intents.get(intent_id)


def mark_intent_used(intent_id: int) -> None:
    if intent_id in _intents:
        _intents[intent_id]["used"] = True