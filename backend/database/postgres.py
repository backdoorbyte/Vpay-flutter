"""
PostgreSQL support for Railway deployment.
"""

import asyncio
import asyncpg
import os

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get the connection pool."""
    global _pool
    if _pool is None:
        raise RuntimeError("PostgreSQL not initialized. Call init_postgres() on startup.")
    return _pool


async def init_postgres() -> asyncpg.Pool:
    """Initialize PostgreSQL connection pool."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    # Railway sometimes uses postgres:// instead of postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    _pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)

    # Verify connection
    async with _pool.acquire() as conn:
        await conn.fetchval("SELECT 1")

    return _pool


async def close_postgres() -> None:
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_sync_connection():
    """
    Synchronous wrapper for code that expects sqlite3-style connection.
    This is a compatibility layer - prefer async methods when possible.
    """
    return _pool