"""
Speech-to-text via Faster-Whisper with Hindi / English / Hinglish support.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

from config import WHISPER_BEAM_SIZE, WHISPER_BEAM_SIZE_FAST, WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    from faster_whisper import WhisperModel

    logger.info("Loading Faster-Whisper model '%s'...", WHISPER_MODEL_SIZE)
    _model = WhisperModel(
        WHISPER_MODEL_SIZE,
        device="cuda" if _cuda_available() else "cpu",
        compute_type="float16" if _cuda_available() else "int8",
    )
    return _model


def _cuda_available() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def _language_hint(lang: Optional[str]) -> Optional[str]:
    if lang is None:
        return None
    mapping = {"en": "en", "hi": "hi", "hinglish": None,
               "hindi": "hi", "english": "en"}
    return mapping.get(lang, None)


def _correct_numbers(text: str) -> str:
    """
    Post-process transcription to correct common number and UPI mishearings.
    Handles:
      - Spaced digit groups: "29 14 2478 894" → "29142478894"
      - UPI @ spoken as "at the", "at the rate", etc.
    """
    import re

    # Exact whole-number mishearings
    exact_corrections = {
        "522": "500",
        "512": "500",
        "532": "500",
        "542": "500",
        "552": "500",
        "562": "500",
        "572": "500",
        "582": "500",
        "592": "500",
        "122": "100",
        "132": "100",
        "142": "100",
        "152": "100",
        "162": "100",
        "172": "100",
        "182": "100",
        "192": "100",
        "seventwo": "",
    }

    for wrong, correct in exact_corrections.items():
        text = re.sub(rf"\b{wrong}\b", correct, text)

    # Collapse spaced digit groups iteratively
    # "29 14 2478 894" → "29142478894" (needed for UPI mobile numbers)
    # "5 2 2" → "522"
    prev = None
    while text != prev:
        prev = text
        text = re.sub(r"(\d+)\s+(\d+)", r"\1\2", text)

    return text


def transcribe_audio(
    wav_path: Path,
    language: Optional[str] = None,
    *,
    fast: bool = False,
) -> Tuple[str, str]:
    """
    Transcribe WAV file.

    fast=True uses beam_size=1 and tuned settings for short confirmation clips.

    If no language hint is provided and auto-detection returns an unexpected
    language (not Hindi/English), retries with Hindi language forced.
    """
    model = _get_model()
    lang_hint = _language_hint(language)
    beam = WHISPER_BEAM_SIZE_FAST if fast else WHISPER_BEAM_SIZE

    segments, info = model.transcribe(
        str(wav_path),
        language=lang_hint,
        task="transcribe",
        vad_filter=False,  # Disable VAD to improve transcription accuracy
        beam_size=beam,
        best_of=2 if fast else 1,
        temperature=0.0,
        condition_on_previous_text=False,
        without_timestamps=True,
    )
    text = " ".join(seg.text.strip() for seg in segments).strip()
    detected = info.language or language
    logger.info(f"Raw transcription: '{text}' (Language: {detected})")

    # If no language hint was given and detected language is not Hindi/English,
    # retry with Hindi forced (common for Hinglish commands)
    if language is None and detected not in ('hi', 'en', 'hindi', 'english'):
        logger.info(f"Detected language '{detected}' is not Hindi/English. Retrying with Hindi...")
        segments_retry, info_retry = model.transcribe(
            str(wav_path),
            language="hi",
            task="transcribe",
            vad_filter=False,
            beam_size=beam,
            best_of=2 if fast else 1,
            temperature=0.0,
            condition_on_previous_text=False,
            without_timestamps=True,
        )
        text_retry = " ".join(seg.text.strip() for seg in segments_retry).strip()
        logger.info(f"Retry transcription (Hindi forced): '{text_retry}'")

        # Use retry if it produced text that looks like Hindi/Hinglish
        if text_retry and (_contains_hindi_words(text_retry) or len(text_retry) > len(text)):
            text = text_retry
            detected = "hi"

    # Apply number correction
    text = _correct_numbers(text)
    logger.info(f"Corrected transcription: '{text}'")

    # Fallback: if transcription returned nothing, try again
    if not text:
        logger.info("Transcription returned empty text for %s. Retrying...", wav_path)
        segments, _ = model.transcribe(
            str(wav_path),
            language=lang_hint,
            task="transcribe",
            vad_filter=False,
            beam_size=beam,
            best_of=2 if fast else 1,
            temperature=0.0,
            condition_on_previous_text=False,
            without_timestamps=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        logger.info(f"Retry transcription: '{text}'")
        text = _correct_numbers(text)
        logger.info(f"Retry corrected transcription: '{text}'")

    return text, detected


def _contains_hindi_words(text: str) -> bool:
    """Check if text contains common Hindi/Hinglish words."""
    hindi_words = {
        'ko', 'kou', 'bhejo', 'bhejiye', 'rupaye', 'rupya', 'sau', 'hazaar',
        'paanch', 'chaar', 'teen', 'do', 'ek', 'rahul', 'priya', 'amit',
        'raahul', 'raagul', 'bhej', 'rupya', 'kar', 'karo', 'liye'
    }
    text_lower = text.lower()
    return any(word in text_lower for word in hindi_words)
