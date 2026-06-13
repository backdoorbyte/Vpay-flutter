"""
SQLite schema for users, voice embeddings, challenges, and transactions.

Only embeddings are stored for voice — never raw audio blobs.
"""

from __future__ import annotations

import aiosqlite

SCHEMA_SQL = """
-- Single demo user; extend with auth in production
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT 'Demo User',
    phone TEXT UNIQUE,
    wallet_balance REAL NOT NULL DEFAULT 10000.0,
    is_voice_enrolled INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Mean ECAPA embedding (192-dim) stored as JSON array
CREATE TABLE IF NOT EXISTS voice_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    embedding_json TEXT NOT NULL,
    sample_count INTEGER NOT NULL DEFAULT 20,
    enrolled_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Face embedding (512-dim) stored as JSON array for verification
CREATE TABLE IF NOT EXISTS face_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    embedding_json TEXT NOT NULL,
    enrolled_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Active challenge for challenge-response flow
CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phrase TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recipient TEXT NOT NULL,
    upi_id TEXT,
    amount REAL NOT NULL,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'success',
    verification_score REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    upi_id TEXT NOT NULL,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_user ON contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(user_id, name_normalized);
"""


async def _migrate_columns(db: aiosqlite.Connection) -> None:
    """Add columns introduced after initial release."""
    cursor = await db.execute("PRAGMA table_info(transactions)")
    cols = {r[1] for r in await cursor.fetchall()}
    if "upi_id" not in cols:
        await db.execute("ALTER TABLE transactions ADD COLUMN upi_id TEXT")

    # Add face enrollment flag to users
    cursor = await db.execute("PRAGMA table_info(users)")
    user_cols = {r[1] for r in await cursor.fetchall()}
    if "is_face_enrolled" not in user_cols:
        await db.execute("ALTER TABLE users ADD COLUMN is_face_enrolled INTEGER NOT NULL DEFAULT 0")


async def apply_schema(db: aiosqlite.Connection) -> None:
    """Execute DDL and seed demo user if missing."""
    await db.executescript(SCHEMA_SQL)
    await _migrate_columns(db)
    cursor = await db.execute("SELECT COUNT(*) AS c FROM users")
    row = await cursor.fetchone()
    if row and row["c"] == 0:
        await db.execute(
            "INSERT INTO users (name, phone, wallet_balance) VALUES (?, ?, ?)",
            ("Demo User", "+919999999999", 10000.0),
        )
    from services.contact_service import seed_demo_contacts

    await seed_demo_contacts(db)
