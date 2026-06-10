"""
POST /transcribe — speech-to-text via Faster-Whisper.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Query, UploadFile

from models.schemas import LanguageCode, TranscribeResponse
from services.whisper_service import transcribe_audio
from utils.audio import cleanup_path, save_upload_to_wav

router = APIRouter(tags=["Speech-to-Text"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(...),
    language: LanguageCode = Query(LanguageCode.en, description="en | hi | hinglish"),
):
    """Convert voice to text; supports Hindi, English, and Hinglish (auto-detect)."""
    wav_path: Path | None = None
    try:
        wav_path = await save_upload_to_wav(audio)
        text, detected = transcribe_audio(wav_path, language.value)
        return TranscribeResponse(text=text, language=detected)
    finally:
        if wav_path:
            cleanup_path(wav_path)
