"""
AASIST anti-spoofing / liveness detection for VPay.
Uses the fine-tuned AASIST model (best_aasist_hinglish.pth).

Detects:
- Replay attacks (recorded voice played back)
- Synthetic/TTS-generated speech
- Voice conversion attacks

Replaces the previous clovaai/aasist download-based approach
with your locally fine-tuned weights.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LIVENESS_THRESHOLD = float(os.getenv("LIVENESS_THRESHOLD", "0.5"))
AASIST_MODEL_PATH = os.getenv(
    "AASIST_MODEL_PATH",
    "pretrained_models/best_aasist_hinglish.pth",
)

# ---------------------------------------------------------------------------
# Lazy-loaded singleton
# ---------------------------------------------------------------------------
_verifier = None
_model_load_failed = False


def _get_verifier():
    """Lazy-initialize the liveness verifier."""
    global _verifier, _model_load_failed

    if _model_load_failed:
        logger.warning("AASIST model unavailable, skipping liveness check")
        return None

    if _verifier is not None:
        return _verifier

    try:
        logger.info("Initializing AASIST liveness verifier...")

        # Import the inference module (contains the fine-tuned model wrapper)
        from services.aasist_inference import LivenessVerifier

        _verifier = LivenessVerifier(
            model_path=AASIST_MODEL_PATH,
            threshold=LIVENESS_THRESHOLD,
        )

        logger.info("AASIST liveness verifier initialized successfully")
        return _verifier

    except Exception as e:
        logger.error(f"Failed to initialize AASIST verifier: {e}")
        logger.warning("AASIST liveness detection will be DISABLED")
        _model_load_failed = True
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_liveness(wav_path: Path) -> Tuple[bool, float]:
    """
    Check if audio is from a real human (not spoofed/replayed).

    Args:
        wav_path: Path to 16kHz mono WAV file

    Returns:
        (is_bonafide, confidence_score)
        - is_bonafide: True if real human speech (not spoof)
        - confidence: 0-1 score (higher = more confident it's real)

    Fallback: If model is unavailable, returns (True, 1.0) to allow
    payment flow to continue (liveness check skipped).
    """
    verifier = _get_verifier()

    # Graceful fallback: if model unavailable, assume liveness passed
    if verifier is None:
        logger.warning(f"Liveness check SKIPPED for {wav_path} (model unavailable)")
        return True, 1.0

    # Run inference via the fine-tuned model
    try:
        is_bonafide, confidence, verdict = verifier.check_audio(str(wav_path))
        logger.info(f"Liveness: bonafide={is_bonafide} conf={confidence:.4f} | {verdict}")
        return is_bonafide, confidence
    except Exception as e:
        logger.error(f"Liveness check error: {e}", exc_info=True)
        # Fail-safe: if inference fails, we reject (security-first)
        return False, 0.0


async def check_liveness_async(wav_path: Path) -> Tuple[bool, float]:
    """
    Async wrapper for check_liveness.
    Runs the model inference in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, check_liveness, wav_path)


def get_liveness_threshold() -> float:
    """Get current liveness threshold from config."""
    return LIVENESS_THRESHOLD
