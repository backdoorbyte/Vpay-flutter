"""
Voice enrollment: accumulate 20 samples, mean-embed, persist to database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Union

import aiosqlite
import asyncpg
import numpy as np

from utils.embeddings import embedding_to_json, mean_embedding

# In-memory buffer per user until 20 samples (demo: user_id=1)
_pending_samples: Dict[int, List[np.ndarray]] = {}
REQUIRED_SAMPLES = 20


def add_sample(user_id: int, embedding: np.ndarray) -> tuple[int, bool]:
    """
    Append embedding to pending buffer.
    Skips embeddings with zero norm (silent/invalid audio).

    Returns:
        (count, enrolled) — enrolled True when 20 samples averaged and ready to save
    """
    if np.linalg.norm(embedding) < 1e-9:
        # Skip silent/invalid samples
        buf = _pending_samples.get(user_id, [])
        count = len(buf)
        return count, False
    if user_id not in _pending_samples:
        _pending_samples[user_id] = []
    buf = _pending_samples[user_id]
    if len(buf) >= REQUIRED_SAMPLES:
        return len(buf), False
    buf.append(embedding)
    count = len(buf)
    return count, count >= REQUIRED_SAMPLES


async def finalize_enrollment(db: Union[aiosqlite.Connection, asyncpg.Pool], user_id: int) -> bool:
    """Average pending embeddings and write to voice_embeddings table."""
    buf = _pending_samples.get(user_id, [])
    if len(buf) < REQUIRED_SAMPLES:
        return False

    mean_emb = mean_embedding(buf)
    emb_json = embedding_to_json(mean_emb)

    if isinstance(db, asyncpg.Pool):
        async with db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO voice_embeddings (user_id, embedding_json, sample_count, enrolled_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT(user_id) DO UPDATE SET
                    embedding_json = EXCLUDED.embedding_json,
                    sample_count = EXCLUDED.sample_count,
                    enrolled_at = EXCLUDED.enrolled_at
                """,
                user_id, emb_json, REQUIRED_SAMPLES, datetime.now(timezone.utc).isoformat(),
            )
            await conn.execute(
                "UPDATE users SET is_voice_enrolled = 1 WHERE id = $1", user_id
            )
    else:
        await db.execute(
            """
            INSERT INTO voice_embeddings (user_id, embedding_json, sample_count, enrolled_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                embedding_json = excluded.embedding_json,
                sample_count = excluded.sample_count,
                enrolled_at = datetime('now')
            """,
            (user_id, emb_json, REQUIRED_SAMPLES),
        )
        await db.execute(
            "UPDATE users SET is_voice_enrolled = 1 WHERE id = ?",
            (user_id,),
        )
        await db.commit()

    _pending_samples[user_id] = []
    return True


def reset_enrollment(user_id: int) -> None:
    """Clear pending samples (e.g. user restarts enrollment)."""
    _pending_samples[user_id] = []


def get_pending_count(user_id: int) -> int:
    return len(_pending_samples.get(user_id, []))


async def clear_stored_enrollment(db: Union[aiosqlite.Connection, asyncpg.Pool], user_id: int) -> None:
    """Remove DB embedding when user re-enrolls."""
    if isinstance(db, asyncpg.Pool):
        async with db.acquire() as conn:
            await conn.execute("DELETE FROM voice_embeddings WHERE user_id = $1", user_id)
            await conn.execute(
                "UPDATE users SET is_voice_enrolled = 0 WHERE id = $1", user_id
            )
    else:
        await db.execute("DELETE FROM voice_embeddings WHERE user_id = ?", (user_id,))
        await db.execute(
            "UPDATE users SET is_voice_enrolled = 0 WHERE id = ?",
            (user_id,),
        )
        await db.commit()
    reset_enrollment(user_id)


async def get_enrollment_status(
    db: Union[aiosqlite.Connection, asyncpg.Pool], user_id: int
) -> dict:
    if isinstance(db, asyncpg.Pool):
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT is_voice_enrolled FROM users WHERE id = $1", user_id
            )
    else:
        cursor = await db.execute(
            "SELECT is_voice_enrolled FROM users WHERE id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

    enrolled_db = bool(row["is_voice_enrolled"]) if row else False
    pending = get_pending_count(user_id)
    if pending > 0:
        samples = pending
    elif enrolled_db:
        samples = REQUIRED_SAMPLES
    else:
        samples = 0
    return {
        "samples_received": samples,
        "samples_required": REQUIRED_SAMPLES,
        "is_voice_enrolled": enrolled_db,
        "pending_in_session": pending > 0,
    }


async def get_enrolled_embedding(
    db: Union[aiosqlite.Connection, asyncpg.Pool], user_id: int
) -> np.ndarray | None:
    from utils.embeddings import embedding_from_json

    if isinstance(db, asyncpg.Pool):
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT embedding_json FROM voice_embeddings WHERE user_id = $1", user_id
            )
    else:
        cursor = await db.execute(
            "SELECT embedding_json FROM voice_embeddings WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

    if not row:
        return None
    return embedding_from_json(row["embedding_json"])


async def refine_embedding(
    db: Union[aiosqlite.Connection, asyncpg.Pool], user_id: int, new_embedding: np.ndarray, score: float
) -> bool:
    """
    Refine stored embedding with a new high-confidence sample.
    Only refines if score is above a high-confidence threshold (e.g., 0.75).
    """
    if score < 0.75:
        return False

    from utils.embeddings import embedding_from_json, embedding_to_json

    if isinstance(db, asyncpg.Pool):
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT embedding_json, sample_count FROM voice_embeddings WHERE user_id = $1", user_id
            )
            if not row:
                return False

            stored_emb = embedding_from_json(row["embedding_json"])
            count = row["sample_count"]

            # Limit max weight to prevent stale profile (drift)
            weight = min(count, 50)

            # Weighted average: (stored * count + new) / (count + 1)
            updated_emb = (stored_emb * weight + new_embedding) / (weight + 1)
            # Re-normalize
            updated_emb = updated_emb / np.linalg.norm(updated_emb)

            emb_json = embedding_to_json(updated_emb)

            await conn.execute(
                """
                UPDATE voice_embeddings
                SET embedding_json = $1, sample_count = sample_count + 1, enrolled_at = $2
                WHERE user_id = $3
                """,
                emb_json, datetime.now(timezone.utc).isoformat(), user_id,
            )
            return True
    else:
        cursor = await db.execute(
            "SELECT embedding_json, sample_count FROM voice_embeddings WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return False

        stored_emb = embedding_from_json(row["embedding_json"])
        count = row["sample_count"]

        # Limit max weight to prevent stale profile (drift)
        weight = min(count, 50)

        # Weighted average: (stored * count + new) / (count + 1)
        updated_emb = (stored_emb * weight + new_embedding) / (weight + 1)
        # Re-normalize
        updated_emb = updated_emb / np.linalg.norm(updated_emb)

        emb_json = embedding_to_json(updated_emb)

        await db.execute(
            """
            UPDATE voice_embeddings
            SET embedding_json = ?, sample_count = sample_count + 1, enrolled_at = datetime('now')
            WHERE user_id = ?
            """,
            (emb_json, user_id),
        )
        await db.commit()
        return True