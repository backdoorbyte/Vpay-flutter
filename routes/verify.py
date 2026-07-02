"""
POST /verify — speaker verification against enrolled ECAPA embedding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import aiosqlite
import asyncpg
from fastapi import APIRouter, Depends, File, UploadFile

from database.connection import get_db
from models.schemas import VerifyResponse
from services import enrollment_service
from services.speaker_service import get_threshold, verify_against_enrolled
from utils.audio import cleanup_path, save_upload_to_wav

router = APIRouter(tags=["Speaker Verification"])

DEFAULT_USER_ID = 1


@router.post("", response_model=VerifyResponse)
async def verify_speaker(
    audio: UploadFile = File(...),
    db: Union[aiosqlite.Connection, asyncpg.Pool] = Depends(get_db),
):
    """
    Compare new voice sample to enrolled embedding.
    Returns cosine similarity score and accept/reject.
    """
    enrolled = await enrollment_service.get_enrolled_embedding(db, DEFAULT_USER_ID)
    if enrolled is None:
        return VerifyResponse(
            verified=False,
            score=0.0,
            threshold=get_threshold(),
            message="Complete voice enrollment first (20 samples)",
        )

    wav_path: Path | None = None
    try:
        wav_path = await save_upload_to_wav(audio)
        accepted, score = verify_against_enrolled(wav_path, enrolled)
        return VerifyResponse(
            verified=accepted,
            score=round(score, 4),
            threshold=get_threshold(),
            message="Speaker verified" if accepted else "Speaker not recognized",
        )
    except Exception as e:
        return VerifyResponse(
            verified=False,
            score=0.0,
            threshold=get_threshold(),
            message=f"Verification error: {e}",
        )
    finally:
        if wav_path:
            cleanup_path(wav_path)