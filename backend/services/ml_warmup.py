"""Preload heavy ML models at startup to avoid first-request latency."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from config import PRELOAD_ML_MODELS

logger = logging.getLogger(__name__)


def preload_models() -> None:
    """Load Whisper + ECAPA in parallel (blocking — call from a thread)."""
    if not PRELOAD_ML_MODELS:
        logger.info("ML preload disabled (PRELOAD_ML_MODELS=false)")
        return

    def _whisper():
        try:
            from services.whisper_service import _get_model
            _get_model()
            logger.info("Whisper model ready")
        except Exception as e:
            logger.warning(f"Whisper model preload failed: {e}. Will load on first use.")

    def _speaker():
        try:
            from services.speaker_service import _get_classifier
            _get_classifier()
            logger.info("ECAPA speaker model ready")
        except Exception as e:
            logger.warning(f"ECAPA speaker model preload failed: {e}. Will load on first use.")

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(_whisper)
        f2 = pool.submit(_speaker)
        f1.result()
        f2.result()
    logger.info("ML model preload complete (check warnings for any failures)")
