"""
Face verification service using DeepFace.
Handles face embedding extraction and comparison.
"""

from __future__ import annotations

import logging
import json
import os
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np

# Set legacy Keras mode before importing DeepFace
os.environ["TF_USE_LEGACY_KERAS"] = "1"

logger = logging.getLogger("vpay")

_embedding_cache = {}  # user_id -> embedding array


def _extract_embedding(image_path: Path) -> Optional[np.ndarray]:
    """Extract face embedding from an image using DeepFace."""
    try:
        from deepface import DeepFace

        # Verify file exists and is readable
        if not image_path.exists():
            logger.error(f"Image file does not exist: {image_path}")
            return None

        file_size = image_path.stat().st_size
        logger.info(f"Processing image: {image_path} ({file_size} bytes)")

        # Use VGG-Face for fast embedding extraction
        # Try with opencv detector first, fallback to ssd if it fails
        try:
            result = DeepFace.represent(
                img_path=str(image_path),
                model_name="VGG-Face",
                detector_backend="opencv",
                enforce_detection=False,
                align=True,
            )
        except Exception as detect_error:
            logger.warning(f"Opencv detection failed, trying ssd: {detect_error}")
            try:
                result = DeepFace.represent(
                    img_path=str(image_path),
                    model_name="VGG-Face",
                    detector_backend="ssd",
                    enforce_detection=False,
                    align=True,
                )
            except Exception as ssd_error:
                logger.error(f"SSD detection also failed: {ssd_error}")
                return None

        if result and len(result) > 0:
            embedding = np.array(result[0]["embedding"])
            # Verify embedding is valid (not all zeros)
            if np.linalg.norm(embedding) > 1e-9:
                logger.info(f"Successfully extracted face embedding (norm={np.linalg.norm(embedding):.4f})")
                return embedding
            else:
                logger.warning("Extracted embedding has zero norm (invalid)")
                return None

        logger.warning("No face detected in image (empty result)")
        return None
    except Exception as e:
        logger.error(f"Face embedding extraction failed: {e}", exc_info=True)
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
        logger.info(f"Starting face enrollment for user {user_id} with image {image_path}")

        embedding = _extract_embedding(image_path)
        if embedding is None:
            logger.warning(f"No valid face embedding extracted for user {user_id}")
            return False, "No face detected. Please ensure your face is clearly visible and well-lit."

        # Store in cache (will be persisted to DB by caller)
        _embedding_cache[user_id] = embedding
        logger.info(f"Face enrollment successful for user {user_id} (embedding norm: {np.linalg.norm(embedding):.4f})")
        return True, "Face enrolled successfully"
    except Exception as e:
        logger.error(f"Face enrollment failed: {e}", exc_info=True)
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