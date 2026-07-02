"""Saved payees: name / phone → UPI ID. PostgreSQL compatible."""

from __future__ import annotations

import re
from typing import Any, Optional

import asyncpg

DEFAULT_USER_ID = 1


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def _phonetic_match(name: str, contact_name: str) -> bool:
    """
    Check if two names are phonetically similar (for Whisper transcription errors).
    Common Hindi/English variations:
    - Rahul ~ Raagul, Raahul
    - Priya ~ Priyaa
    - Amit ~ Ameet, Amith
    """
    name = _normalize_name(name)
    contact = _normalize_name(contact_name)

    # Direct match
    if name == contact:
        return True

    # Normalize common vowel variations in Hindi transcription
    name_normalized = (name
        .replace("aa", "a").replace("ee", "i").replace("ii", "i")
        .replace("oo", "u").replace("uu", "u").replace("ae", "e")
        .replace("aa", "a"))
    contact_normalized = (contact
        .replace("aa", "a").replace("ee", "i").replace("ii", "i")
        .replace("oo", "u").replace("uu", "u").replace("ae", "e")
        .replace("aa", "a"))

    if name_normalized == contact_normalized:
        return True

    # Levenshtein distance within 1-2 edits for short names
    max_len = max(len(name), len(contact))
    if max_len <= 5:
        return _levenshtein_distance(name, contact) <= 1
    elif max_len <= 8:
        return _levenshtein_distance(name, contact) <= 2
    else:
        return _levenshtein_distance(name, contact) <= 3


async def list_contacts(
    pool: asyncpg.Pool, user_id: int = DEFAULT_USER_ID
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, upi_id, phone
            FROM contacts WHERE user_id = $1
            ORDER BY LOWER(name)
            """,
            user_id,
        )
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "upi_id": r["upi_id"],
                "phone": r["phone"],
            }
            for r in rows
        ]


async def add_contact(
    pool: asyncpg.Pool,
    name: str,
    upi_id: str,
    phone: Optional[str] = None,
    user_id: int = DEFAULT_USER_ID,
) -> dict[str, Any]:
    phone_digits = _digits_only(phone) if phone else None
    if phone_digits and len(phone_digits) == 10:
        phone = phone_digits
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO contacts (user_id, name, name_normalized, upi_id, phone)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            user_id, name.strip(), _normalize_name(name), upi_id.lower(), phone,
        )
        return {
            "id": row["id"],
            "name": name.strip(),
            "upi_id": upi_id.lower(),
            "phone": phone,
        }


async def delete_contact(
    pool: asyncpg.Pool, contact_id: int, user_id: int = DEFAULT_USER_ID
) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM contacts WHERE id = $1 AND user_id = $2",
            contact_id, user_id,
        )
        # result is a string like "DELETE 1" or "DELETE 0"
        return result.startswith("DELETE 1")


async def find_by_name(
    pool: asyncpg.Pool, name: str, user_id: int = DEFAULT_USER_ID
) -> Optional[dict[str, Any]]:
    norm = _normalize_name(name)

    # 1. Exact match on normalized name
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, upi_id, phone FROM contacts
            WHERE user_id = $1 AND name_normalized = $2
            LIMIT 1
            """,
            user_id, norm,
        )
        if row:
            return dict(row)

        # 2. Prefix match
        row = await conn.fetchrow(
            """
            SELECT id, name, upi_id, phone FROM contacts
            WHERE user_id = $1 AND name_normalized LIKE $2
            LIMIT 1
            """,
            user_id, f"{norm}%",
        )
        if row:
            return dict(row)

        # 3. Fuzzy phonetic match (for Whisper transcription variations)
        all_rows = await conn.fetch(
            """
            SELECT id, name, upi_id, phone FROM contacts
            WHERE user_id = $1
            ORDER BY LOWER(name)
            """,
            user_id,
        )
        for row in all_rows:
            if _phonetic_match(name, row["name"]):
                return dict(row)

    return None


async def find_by_phone(
    pool: asyncpg.Pool, phone: str, user_id: int = DEFAULT_USER_ID
) -> Optional[dict[str, Any]]:
    digits = _digits_only(phone)
    if len(digits) != 10:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, upi_id, phone FROM contacts
            WHERE user_id = $1 AND (phone = $2 OR upi_id LIKE $3)
            LIMIT 1
            """,
            user_id, digits, f"{digits}@%",
        )
        return dict(row) if row else None


async def find_by_upi(
    pool: asyncpg.Pool, upi_id: str, user_id: int = DEFAULT_USER_ID
) -> Optional[dict[str, Any]]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, upi_id, phone FROM contacts
            WHERE user_id = $1 AND upi_id = $2
            LIMIT 1
            """,
            user_id, upi_id.lower(),
        )
        return dict(row) if row else None


async def seed_demo_contacts(pool: asyncpg.Pool, user_id: int = DEFAULT_USER_ID) -> None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) AS c FROM contacts WHERE user_id = $1", user_id
        )
        if row and row["c"] > 0:
            return
        demos = [
            ("Rahul", "rahul@ybl", "9876543210"),
            ("Priya", "priya@paytm", "9123456780"),
            ("Amit", "9988776655@ybl", "9988776655"),
        ]
        for name, upi, phone in demos:
            await conn.execute(
                """
                INSERT INTO contacts (user_id, name, name_normalized, upi_id, phone)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, name, _normalize_name(name), upi, phone,
            )