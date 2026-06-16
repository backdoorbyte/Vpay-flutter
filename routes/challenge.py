"""
Challenge-response endpoints for secure voice payments.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile

import aiosqlite
from config import PHRASE_MATCH_MIN_RATIO
from database.connection import get_db
from models.schemas import (
    ChallengeResponse,
    ChallengeVerifyResponse,
    LanguageCode,
)
from services import challenge_service, enrollment_service
from services.speaker_service import get_threshold, verify_against_enrolled
from services.whisper_service import transcribe_audio
from utils.audio import cleanup_path, save_upload_to_wav
from utils.phrase_match import phrase_matches

router = APIRouter(tags=["Challenge-Response"])

DEFAULT_USER_ID = 1

# Challenges that passed voice + phrase check (valid until payment consumes them)
_verified_challenges: dict[int, float] = {}


@router.post("", response_model=ChallengeResponse)
async def create_challenge(
    language: LanguageCode = Query(LanguageCode.en),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Generate a random phrase the user must repeat before payment."""
    cid, phrase, ttl = await challenge_service.create_challenge(
        db, DEFAULT_USER_ID, language.value
    )
    return ChallengeResponse(
        challenge_id=cid, phrase=phrase, expires_in_seconds=ttl
    )


@router.post("/verify", response_model=ChallengeVerifyResponse)
async def verify_challenge(
    challenge_id: int = Query(...),
    language: LanguageCode = Query(LanguageCode.en),
    audio: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Verify user repeated the challenge phrase and matches enrolled speaker.
    Does not mark challenge used — payment endpoint consumes it.
    """
    enrolled = await enrollment_service.get_enrolled_embedding(db, DEFAULT_USER_ID)
    if enrolled is None:
        return ChallengeVerifyResponse(
            verified=False,
            score=0.0,
            phrase_match_score=0.0,
            threshold=get_threshold(),
            message="Complete voice enrollment first",
        )

    cursor = await db.execute(
        "SELECT phrase, expires_at, used FROM challenges WHERE id = ? AND user_id = ?",
        (challenge_id, DEFAULT_USER_ID),
    )
    row = await cursor.fetchone()
    if not row:
        return ChallengeVerifyResponse(
            verified=False,
            score=0.0,
            phrase_match_score=0.0,
            threshold=get_threshold(),
            message="Challenge not found",
        )
    if row["used"]:
        return ChallengeVerifyResponse(
            verified=False,
            score=0.0,
            phrase_match_score=0.0,
            threshold=get_threshold(),
            message="Challenge already used",
        )

    from datetime import datetime

    if datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
        return ChallengeVerifyResponse(
            verified=False,
            score=0.0,
            phrase_match_score=0.0,
            threshold=get_threshold(),
            message="Challenge expired",
        )

    wav_path: Path | None = None
    try:
        wav_path = await save_upload_to_wav(audio)
        text, _ = transcribe_audio(wav_path, language.value)
        phrase_ok, phrase_score = phrase_matches(
            row["phrase"], text, PHRASE_MATCH_MIN_RATIO
        )
        speaker_ok, score = verify_against_enrolled(wav_path, enrolled)
        verified = phrase_ok and speaker_ok
        if verified:
            _verified_challenges[challenge_id] = score

        msg_parts = []
        if not phrase_ok:
            msg_parts.append("Phrase did not match")
        if not speaker_ok:
            msg_parts.append("Speaker not recognized")
        message = (
            "Challenge verified"
            if verified
            else "; ".join(msg_parts) or "Verification failed"
        )

        return ChallengeVerifyResponse(
            verified=verified,
            score=round(score, 4),
            phrase_match_score=round(phrase_score, 4),
            transcribed_text=text,
            threshold=get_threshold(),
            message=message,
        )
    except Exception as e:
        return ChallengeVerifyResponse(
            verified=False,
            score=0.0,
            phrase_match_score=0.0,
            threshold=get_threshold(),
            message=str(e),
        )
    finally:
        if wav_path:
            cleanup_path(wav_path)


def is_challenge_verified(challenge_id: int) -> bool:
    return challenge_id in _verified_challenges


def pop_verified_score(challenge_id: int) -> float | None:
    return _verified_challenges.pop(challenge_id, None)
