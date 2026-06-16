"""
Speaker verification via SpeechBrain ECAPA-TDNN.

Model: speechbrain/spkrec-ecapa-voxceleb
Lazy-loaded singleton to avoid startup cost on import.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from config import VERIFY_THRESHOLD
from utils.embeddings import cosine_similarity

logger = logging.getLogger(__name__)

_classifier = None


def _get_classifier():
    """Load ECAPA-TDNN once."""
    global _classifier
    if _classifier is not None:
        return _classifier
    from speechbrain.inference.speaker import EncoderClassifier

    logger.info("Loading ECAPA-TDNN (first request may take a minute)...")
    _classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb",
        run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"},
    )
    return _classifier


def extract_embedding(wav_path: Path) -> np.ndarray:
    """
    Generate 192-dimensional speaker embedding from a WAV file.

    Args:
        wav_path: 16 kHz mono WAV path

    Returns:
        L2-normalized embedding vector
    """
    classifier = _get_classifier()
    # Pass a relative path (from backend root) to avoid Windows path issues
    # where some loaders may incorrectly prefix the working directory.
    backend_root = Path(__file__).resolve().parents[1]
    try:
        wav_for_loader = str(wav_path.relative_to(backend_root))
    except Exception:
        wav_for_loader = str(wav_path)
    signal = classifier.load_audio(wav_for_loader)
    with torch.no_grad():
        emb = classifier.encode_batch(signal)
    vec = emb.squeeze().cpu().numpy().astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm < 1e-9:
        logger.warning(f"Extracted embedding norm is zero for {wav_path}. Audio might be silent or too short.")
        return np.zeros(192, dtype=np.float32)
    vec = vec / norm
    return vec


def verify_against_enrolled(
    probe_path: Path, enrolled: np.ndarray, *, return_embedding: bool = False
) -> tuple[bool, float] | tuple[bool, float, np.ndarray]:
    """
    Compare probe audio embedding to stored enrollment.

    Returns:
        (accepted, cosine_score) or (accepted, cosine_score, probe_embedding) if return_embedding=True
    """
    probe = extract_embedding(probe_path)
    score = cosine_similarity(probe, enrolled)
    accepted = score >= VERIFY_THRESHOLD
    if return_embedding:
        return accepted, score, probe
    return accepted, score


def get_threshold() -> float:
    return VERIFY_THRESHOLD
