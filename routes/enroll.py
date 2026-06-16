"""
POST /enroll — accept voice sample, build ECAPA embedding, progress toward 20 samples.
Supports one-shot long recording with chunking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import aiosqlite
import asyncpg
import logging
from fastapi import APIRouter, Depends, File, Form, UploadFile

from config import ENROLLMENT_CHUNK_DURATION_SEC
from database.connection import get_db
from models.schemas import EnrollResponse, EnrollStatusResponse
from services import enrollment_service
from services.speaker_service import extract_embedding
from utils.audio import chunk_audio, cleanup_path, save_upload_to_wav

router = APIRouter(tags=["Voice Enrollment"])
logger = logging.getLogger("vpay")

DEFAULT_USER_ID = 1


@router.post("", response_model=EnrollResponse)
async def enroll_voice_sample(
    audio: UploadFile = File(..., description="Voice sample (webm/wav)"),
    mode: str = Form("single", description="Enrollment mode: 'single' (one-shot) or 'multi' (traditional)"),
    db: Union[aiosqlite.Connection, asyncpg.Pool] = Depends(get_db),
):
    """
    Upload enrollment sample(s).

    - mode='single': One long recording (45-60s) that gets chunked automatically
    - mode='multi': Traditional multiple short samples

    After 20 samples, mean embedding is stored in DB.
    """
    wav_path: Path | None = None
    chunk_paths: list[Path] = []

    try:
        wav_path = await save_upload_to_wav(audio)

        if mode == "single":
            # One-shot enrollment: chunk the long recording
            chunk_paths = chunk_audio(wav_path, ENROLLMENT_CHUNK_DURATION_SEC)

            # Extract embeddings from all chunks
            embeddings = []
            for chunk_path in chunk_paths:
                emb = extract_embedding(chunk_path)
                embeddings.append(emb)

            logger.info(f"Extracted {len(embeddings)} embeddings from chunks")

            # Add all embeddings at once
            count = 0
            ready = False
            for emb in embeddings:
                count, ready = enrollment_service.add_sample(DEFAULT_USER_ID, emb)

            logger.info(f"Final count: {count}, ready: {ready}, required: {enrollment_service.REQUIRED_SAMPLES}")

        else:
            # Traditional multi-sample enrollment
            embedding = extract_embedding(wav_path)
            count, ready = enrollment_service.add_sample(DEFAULT_USER_ID, embedding)

        # Finalize enrollment if threshold reached
        enrolled = False
        if ready:
            enrolled = await enrollment_service.finalize_enrollment(db, DEFAULT_USER_ID)

        return EnrollResponse(
            success=True,
            message=(
                "Voice profile created successfully"
                if enrolled
                else f"Sample {count}/{enrollment_service.REQUIRED_SAMPLES} recorded"
            ),
            samples_received=count,
            samples_required=enrollment_service.REQUIRED_SAMPLES,
            enrolled=enrolled,
        )
    except Exception as e:
        return EnrollResponse(
            success=False,
            message=str(e),
            samples_received=len(
                enrollment_service._pending_samples.get(DEFAULT_USER_ID, [])
            ),
            enrolled=False,
        )
    finally:
        if wav_path:
            cleanup_path(wav_path)
        for chunk_path in chunk_paths:
            cleanup_path(chunk_path)


@router.get("/status", response_model=EnrollStatusResponse)
async def enrollment_status(db: Union[aiosqlite.Connection, asyncpg.Pool] = Depends(get_db)):
    """Current enrollment progress and whether voice profile exists."""
    status = await enrollment_service.get_enrollment_status(db, DEFAULT_USER_ID)
    return EnrollStatusResponse(**status)


@router.delete("/reset")
async def reset_enrollment(db: Union[aiosqlite.Connection, asyncpg.Pool] = Depends(get_db)):
    """Clear in-memory buffer and stored embedding for re-enrollment."""
    await enrollment_service.clear_stored_enrollment(db, DEFAULT_USER_ID)
    return {"success": True, "message": "Enrollment reset; record 20 new samples"}