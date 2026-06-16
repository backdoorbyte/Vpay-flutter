"""
PostgreSQL support for Railway/Render deployment.
"""

import asyncio
import asyncpg
import os
import logging
import ssl

logger = logging.getLogger(__name__)

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

    # Debug: log what we got (mask password for security)
    if database_url:
        masked_url = database_url.split("@")[-1] if "@" in database_url else "invalid"
        logger.info(f"DATABASE_URL found: postgresql://***@{masked_url}")
    else:
        logger.error("DATABASE_URL is NOT set!")
        raise ValueError("DATABASE_URL environment variable is not set. "
                        "Add it in Render dashboard: Environment → DATABASE_URL")

    # Railway/Render sometimes uses postgres:// instead of postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    logger.info(f"Connecting to PostgreSQL...")

    # Supabase requires SSL - use a permissive SSL context to accept their certificate chain
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    _pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        ssl=ssl_context
    )

    # Verify connection
    async with _pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        logger.info(f"PostgreSQL connected successfully: {result}")

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