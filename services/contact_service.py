"""Saved payees: name / phone → UPI ID."""

from __future__ import annotations

import re
from typing import Any, Optional

import aiosqlite

DEFAULT_USER_ID = 1


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value)


async def list_contacts(
    db: aiosqlite.Connection, user_id: int = DEFAULT_USER_ID
) -> list[dict[str, Any]]:
    cursor = await db.execute(
        """
        SELECT id, name, upi_id, phone
        FROM contacts WHERE user_id = ?
        ORDER BY name COLLATE NOCASE
        """,
        (user_id,),
    )
    rows = await cursor.fetchall()
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
    db: aiosqlite.Connection,
    name: str,
    upi_id: str,
    phone: Optional[str] = None,
    user_id: int = DEFAULT_USER_ID,
) -> dict[str, Any]:
    phone_digits = _digits_only(phone) if phone else None
    if phone_digits and len(phone_digits) == 10:
        phone = phone_digits
    cursor = await db.execute(
        """
        INSERT INTO contacts (user_id, name, name_normalized, upi_id, phone)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, name.strip(), _normalize_name(name), upi_id.lower(), phone),
    )
    await db.commit()
    return {
        "id": cursor.lastrowid,
        "name": name.strip(),
        "upi_id": upi_id.lower(),
        "phone": phone,
    }


async def delete_contact(
    db: aiosqlite.Connection, contact_id: int, user_id: int = DEFAULT_USER_ID
) -> bool:
    cursor = await db.execute(
        "DELETE FROM contacts WHERE id = ? AND user_id = ?",
        (contact_id, user_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def find_by_name(
    db: aiosqlite.Connection, name: str, user_id: int = DEFAULT_USER_ID
) -> Optional[dict[str, Any]]:
    norm = _normalize_name(name)
    cursor = await db.execute(
        """
        SELECT id, name, upi_id, phone FROM contacts
        WHERE user_id = ? AND name_normalized = ?
        LIMIT 1
        """,
        (user_id, norm),
    )
    row = await cursor.fetchone()
    if row:
        return dict(row)

    cursor = await db.execute(
        """
        SELECT id, name, upi_id, phone FROM contacts
        WHERE user_id = ? AND name_normalized LIKE ?
        LIMIT 1
        """,
        (user_id, f"{norm}%"),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def find_by_phone(
    db: aiosqlite.Connection, phone: str, user_id: int = DEFAULT_USER_ID
) -> Optional[dict[str, Any]]:
    digits = _digits_only(phone)
    if len(digits) != 10:
        return None
    cursor = await db.execute(
        """
        SELECT id, name, upi_id, phone FROM contacts
        WHERE user_id = ? AND (phone = ? OR upi_id LIKE ?)
        LIMIT 1
        """,
        (user_id, digits, f"{digits}@%"),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def find_by_upi(
    db: aiosqlite.Connection, upi_id: str, user_id: int = DEFAULT_USER_ID
) -> Optional[dict[str, Any]]:
    cursor = await db.execute(
        """
        SELECT id, name, upi_id, phone FROM contacts
        WHERE user_id = ? AND upi_id = ?
        LIMIT 1
        """,
        (user_id, upi_id.lower()),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def seed_demo_contacts(db: aiosqlite.Connection, user_id: int = DEFAULT_USER_ID) -> None:
    cursor = await db.execute(
        "SELECT COUNT(*) AS c FROM contacts WHERE user_id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    if row and row["c"] > 0:
        return
    demos = [
        ("Rahul", "rahul@ybl", "9876543210"),
        ("Priya", "priya@paytm", "9123456780"),
        ("Amit", "9988776655@ybl", "9988776655"),
    ]
    for name, upi, phone in demos:
        await db.execute(
            """
            INSERT INTO contacts (user_id, name, name_normalized, upi_id, phone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, _normalize_name(name), upi, phone),
        )
    await db.commit()
