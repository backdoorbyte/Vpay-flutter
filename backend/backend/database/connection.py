"""
SQLite connection and lifecycle for VPay.

Uses aiosqlite for async FastAPI handlers. A single DB file lives under
backend/data/vpay.db (created on first startup).

For Railway/PostgreSQL: Set DATABASE_URL environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite
import logging
logger = logging.getLogger(__name__)

# Check if DATABASE_URL is set (Railway PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

# Project root: backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "vpay.db"

_connection: aiosqlite.Connection | None = None
# For PostgreSQL support
_pg_pool = None


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """FastAPI dependency: yields the shared connection."""
    global _connection
    if _connection is None:
        raise RuntimeError("Database not initialized. Call init_db() on startup.")
    yield _connection


async def init_db() -> None:
    """Create data directory, open connection, run schema migrations."""
    global _connection, _pg_pool

    if DATABASE_URL:
        # Railway PostgreSQL mode
        logger.info("Using PostgreSQL database (Railway)")
        from database.postgres import init_postgres
        _pg_pool = await init_postgres()
    else:
        # Local SQLite mode
        logger.info("Using SQLite database (local)")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _connection = await aiosqlite.connect(str(DB_PATH))
        _connection.row_factory = aiosqlite.Row
        await _connection.execute("PRAGMA foreign_keys = ON")

    from database.schema import apply_schema
    await apply_schema(_connection or _pg_pool)
    if _connection:
        await _connection.commit()


async def close_db() -> None:
    """Close connection on application shutdown."""
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None
