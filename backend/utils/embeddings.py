"""
Embedding math: cosine similarity and mean aggregation for enrollment.
"""

from __future__ import annotations

import json
from typing import List

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return similarity in [0, 1] from L2-normalized vectors."""
    a = np.asarray(a, dtype=np.float32).flatten()
    b = np.asarray(b, dtype=np.float32).flatten()
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    sim = float(np.dot(a, b) / (norm_a * norm_b))
    return max(0.0, min(1.0, sim))


def mean_embedding(embeddings: List[np.ndarray]) -> np.ndarray:
    """Average multiple speaker embeddings and L2-normalize."""
    stack = np.stack([e.flatten() for e in embeddings], axis=0)
    mean = stack.mean(axis=0)
    norm = np.linalg.norm(mean)
    if norm > 1e-9:
        mean = mean / norm
    return mean.astype(np.float32)


def embedding_to_json(vec: np.ndarray) -> str:
    return json.dumps(vec.flatten().tolist())


def embedding_from_json(payload: str) -> np.ndarray:
    return np.array(json.loads(payload), dtype=np.float32)
