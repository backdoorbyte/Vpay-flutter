"""Wallet and transaction history endpoints."""

from __future__ import annotations

from typing import Union

import aiosqlite
import asyncpg
from fastapi import APIRouter, Depends

from database.connection import get_db
from models.schemas import TransactionListResponse, WalletResponse
from services import payment_service

router = APIRouter(tags=["Wallet"])


@router.get("", response_model=WalletResponse)
async def get_wallet(db: Union[aiosqlite.Connection, asyncpg.Pool] = Depends(get_db)):
    data = await payment_service.get_wallet(db)
    return WalletResponse(
        balance=data["balance"],
        is_voice_enrolled=data["is_voice_enrolled"],
        user_name=data["user_name"],
    )


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(db: Union[aiosqlite.Connection, asyncpg.Pool] = Depends(get_db)):
    txs = await payment_service.list_transactions(db)
    return TransactionListResponse(transactions=txs)