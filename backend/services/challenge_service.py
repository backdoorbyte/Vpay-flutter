"""
Challenge-response phrases for secure voice payment.
"""

from __future__ import annotations

import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Union, Tuple

import aiosqlite
import asyncpg

from config import CHALLENGE_TTL_SECONDS

PHRASES_EN = [
    "My voice is my password",
    "Confirm payment with my voice",
    "VPay secure transfer now",
    "I authorize this transaction",
]

PHRASES_HI = [
    "meri awaaz meri pehchaan hai",
    "bhugtan ki pushti karo",
    "VPay surakshit bhugtan",
]

PHRASES_HINGLISH = [
    "mera voice mera password hai",
    "payment confirm karo abhi",
    "VPay se paise bhej do safely",
]


async def create_challenge(
    db: Union[aiosqlite.Connection, asyncpg.Pool], user_id: int, language: str = "en"
) -> Tuple[int, str, int]:
    """
    Insert random challenge phrase; return id, phrase, ttl.
    """
    pools = {"en": PHRASES_EN, "hi": PHRASES_HI, "hinglish": PHRASES_HINGLISH}
    pool = pools.get(language, PHRASES_EN)
    phrase = random.choice(pool)
    # Add numeric nonce to reduce replay
    nonce = secrets.randbelow(9000) + 1000
    full_phrase = f"{phrase} {nonce}"

    expires = datetime.now(timezone.utc) + timedelta(seconds=CHALLENGE_TTL_SECONDS)

    if isinstance(db, asyncpg.Pool):
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO challenges (user_id, phrase, expires_at)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                user_id, full_phrase, expires.isoformat(),
            )
            return row["id"], full_phrase, CHALLENGE_TTL_SECONDS
    else:
        cursor = await db.execute(
            """
            INSERT INTO challenges (user_id, phrase, expires_at)
            VALUES (?, ?, ?)
            """,
            (user_id, full_phrase, expires.isoformat()),
        )
        await db.commit()
        return cursor.lastrowid, full_phrase, CHALLENGE_TTL_SECONDS


async def validate_challenge(
    db: Union[aiosqlite.Connection, asyncpg.Pool], challenge_id: int, user_id: int
) -> Tuple[bool, str]:
    """Mark challenge used if valid and not expired."""
    if isinstance(db, asyncpg.Pool):
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT phrase, expires_at, used FROM challenges WHERE id = $1 AND user_id = $2",
                challenge_id, user_id,
            )
            if not row:
                return False, "Challenge not found"
            if row["used"]:
                return False, "Challenge already used"
            expires = datetime.fromisoformat(row["expires_at"])
            if datetime.now(timezone.utc) > expires:
                return False, "Challenge expired"
            await conn.execute(
                "UPDATE challenges SET used = 1 WHERE id = $1", challenge_id
            )
            return True, row["phrase"]
    else:
        cursor = await db.execute(
            "SELECT phrase, expires_at, used FROM challenges WHERE id = ? AND user_id = ?",
            (challenge_id, user_id),
        )
        row = await cursor.fetchone()
        if not row:
            return False, "Challenge not found"
        if row["used"]:
            return False, "Challenge already used"
        expires = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires:
            return False, "Challenge expired"
        await db.execute("UPDATE challenges SET used = 1 WHERE id = ?", (challenge_id,))
        await db.commit()
        return True, row["phrase"]