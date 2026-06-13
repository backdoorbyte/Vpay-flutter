"""
Face verification service using DeepFace.
Handles face embedding extraction and comparison.
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np

logger = logging.getLogger("vpay")

_embedding_cache = {}  # user_id -> embedding array


def _extract_embedding(image_path: Path) -> Optional[np.ndarray]:
    """Extract face embedding from an image using DeepFace."""
    try:
        from deepface import DeepFace
        # Use VGG-Face for fast embedding extraction
        result = DeepFace.represent(
            img_path=str(image_path),
            model_name="VGG-Face",
            detector_backend="opencv",
            enforce_detection=False,
        )
        if result and len(result) > 0:
            return np.array(result[0]["embedding"])
        return None
    except Exception as e:
        logger.error(f"Face embedding extraction failed: {e}")
        return None


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings."""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


async def enroll_face(user_id: int, image_path: Path) -> Tuple[bool, str]:
    """
    Enroll a face for a user.
    Returns (success, message).
    """
    try:
        embedding = _extract_embedding(image_path)
        if embedding is None:
            return False, "No face detected in the image"

        # Store in cache (will be persisted to DB by caller)
        _embedding_cache[user_id] = embedding
        return True, "Face enrolled successfully"
    except Exception as e:
        logger.error(f"Face enrollment failed: {e}")
        return False, f"Enrollment failed: {str(e)}"


async def verify_face(user_id: int, image_path: Path, threshold: float = 0.6) -> Tuple[bool, float, str]:
    """
    Verify a face against the enrolled embedding.
    Returns (is_match, confidence, message).
    Threshold: cosine similarity >= 0.6 is considered a match.
    """
    try:
        # Check if user has enrolled face
        enrolled_embedding = _embedding_cache.get(user_id)
        if enrolled_embedding is None:
            # Try to load from DB (fallback)
            import aiosqlite
            from database.connection import get_db
            # This is a simplified version - in production, load from DB properly
            logger.warning(f"No face embedding cached for user {user_id}")
            return False, 0.0, "Face not enrolled"

        # Extract embedding from probe image
        probe_embedding = _extract_embedding(image_path)
        if probe_embedding is None:
            return False, 0.0, "No face detected"

        # Calculate similarity
        similarity = _cosine_similarity(enrolled_embedding, probe_embedding)
        logger.info(f"Face verification similarity: {similarity:.4f} (threshold: {threshold})")

        is_match = similarity >= threshold

        if is_match:
            return True, similarity, f"Face verified (confidence: {similarity:.2%})"
        else:
            return False, similarity, f"Face mismatch (confidence: {similarity:.2%})"
    except Exception as e:
        logger.error(f"Face verification failed: {e}")
        return False, 0.0, f"Verification failed: {str(e)}"


def get_cached_embedding(user_id: int) -> Optional[List[float]]:
    """Get cached embedding for a user (for DB persistence)."""
    emb = _embedding_cache.get(user_id)
    if emb is not None:
        return emb.tolist()
    return None


def load_embedding(user_id: int, embedding_list: List[float]) -> None:
    """Load embedding from DB into cache."""
    _embedding_cache[user_id] = np.array(embedding_list)


def clear_embedding(user_id: int) -> None:
    """Clear cached embedding (for reset)."""
    if user_id in _embedding_cache:
        del _embedding_cache[user_id]