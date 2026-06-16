"""
Mock wallet and transaction ledger — no real banking APIs.
"""

from __future__ import annotations

from typing import List, Optional

import aiosqlite

from models.schemas import TransactionItem


async def get_wallet(db: aiosqlite.Connection, user_id: int = 1) -> dict:
    cursor = await db.execute(
        "SELECT name, wallet_balance, is_voice_enrolled FROM users WHERE id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise ValueError("User not found")
    return {
        "user_name": row["name"],
        "balance": float(row["wallet_balance"]),
        "is_voice_enrolled": bool(row["is_voice_enrolled"]),
    }


async def process_payment(
    db: aiosqlite.Connection,
    user_id: int,
    recipient: str,
    upi_id: str,
    amount: float,
    note: Optional[str],
    verification_score: float,
) -> tuple[bool, str, float, Optional[int]]:
    """
    Deduct amount if balance sufficient; record transaction.

    Returns:
        (success, message, new_balance, transaction_id)
    """
    wallet = await get_wallet(db, user_id)
    balance = wallet["balance"]
    if amount > balance:
        return False, "Insufficient balance", balance, None

    new_balance = balance - amount
    await db.execute(
        "UPDATE users SET wallet_balance = ? WHERE id = ?",
        (new_balance, user_id),
    )
    cursor = await db.execute(
        """
        INSERT INTO transactions (user_id, recipient, upi_id, amount, note, status, verification_score)
        VALUES (?, ?, ?, ?, ?, 'success', ?)
        """,
        (user_id, recipient, upi_id, amount, note, verification_score),
    )
    tx_id = cursor.lastrowid
    await db.commit()
    return True, "Payment successful", new_balance, tx_id


async def list_transactions(
    db: aiosqlite.Connection, user_id: int = 1, limit: int = 50
) -> List[TransactionItem]:
    cursor = await db.execute(
        """
        SELECT id, recipient, upi_id, amount, note, status, verification_score, created_at
        FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """,
        (user_id, limit),
    )
    rows = await cursor.fetchall()
    return [
        TransactionItem(
            id=r["id"],
            recipient=r["recipient"],
            upi_id=r["upi_id"],
            amount=float(r["amount"]),
            note=r["note"],
            status=r["status"],
            verification_score=r["verification_score"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
