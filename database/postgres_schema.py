"""
PostgreSQL schema for users, voice embeddings, challenges, and transactions.
"""

import asyncpg

SCHEMA_SQL = """
-- Single demo user; extend with auth in production
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'Demo User',
    phone TEXT UNIQUE,
    wallet_balance REAL NOT NULL DEFAULT 10000.0,
    is_voice_enrolled INTEGER NOT NULL DEFAULT 0,
    is_face_enrolled INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Mean ECAPA embedding (192-dim) stored as JSON array
CREATE TABLE IF NOT EXISTS voice_embeddings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    embedding_json TEXT NOT NULL,
    sample_count INTEGER NOT NULL DEFAULT 20,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Face embedding (512-dim) stored as JSON array for verification
CREATE TABLE IF NOT EXISTS face_embeddings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    embedding_json TEXT NOT NULL,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Active challenge for challenge-response flow
CREATE TABLE IF NOT EXISTS challenges (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phrase TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient TEXT NOT NULL,
    upi_id TEXT,
    amount REAL NOT NULL,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'success',
    verification_score REAL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    upi_id TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_user ON contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(user_id, name_normalized);
"""


async def apply_schema(pool: asyncpg.Pool) -> None:
    """Execute DDL and seed demo user if missing."""
    # Execute schema (asyncpg doesn't support executescript, so we split by semicolons)
    statements = [stmt.strip() for stmt in SCHEMA_SQL.split(';') if stmt.strip()]
    async with pool.acquire() as conn:
        for stmt in statements:
            await conn.execute(stmt)

        # Check if demo user exists
        row = await conn.fetchrow("SELECT COUNT(*) as c FROM users")
        if row and row["c"] == 0:
            await conn.execute(
                "INSERT INTO users (name, phone, wallet_balance) VALUES ($1, $2, $3)",
                "Demo User", "+919999999999", 10000.0,
            )

    # Seed demo contacts
    from services.contact_service import seed_demo_contacts
    await seed_demo_contacts(pool)