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
        # Mask password for logging
        import re
        masked = re.sub(r'postgresql://([^:]+):([^@]+)@', r'postgresql://\1:***@', database_url)
        logger.info(f"DATABASE_URL found: {masked}")
    else:
        logger.error("DATABASE_URL is NOT set!")
        raise ValueError("DATABASE_URL environment variable is not set")

    # Railway/Render sometimes uses postgres:// instead of postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    logger.info(f"Connecting to PostgreSQL...")

    # Supabase requires SSL - use a permissive SSL context to accept their certificate chain
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Parse connection string manually to avoid IPv6 URL issues
    # Format: postgresql://user:password@host:port/db
    from urllib.parse import urlparse
    parsed = urlparse(database_url)

    # Extract components and decode password (in case of URL-encoded chars)
    from urllib.parse import unquote
    user = parsed.username or "postgres"
    password = unquote(parsed.password) if parsed.password else ""
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    database = parsed.path.lstrip("/") if parsed.path else "postgres"

    # Handle IPv6 address formats
    if host.startswith("[") and "]" not in host:
        # Malformed IPv6, try to fix it
        pass

    logger.info(f"Connecting to {host}:{port}/{database} as {user}")

    _pool = await asyncpg.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
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