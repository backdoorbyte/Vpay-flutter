"""
VPay API — Voice-Based Payment Authentication System.

Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database.connection import close_db, init_db
from routes import (
    challenge,
    contacts,
    enroll,
    parse,
    payment,
    payment_intent,
    qr,
    transcribe,
    verify,
    voice_pay,
    wallet,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vpay")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing VPay database...")
    await init_db()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _preload_ml)
    yield
    await close_db()
    logger.info("VPay shutdown complete.")


def _preload_ml() -> None:
    from services.ml_warmup import preload_models

    preload_models()


app = FastAPI(
    title="VPay API",
    description="Voice-based payment authentication with speaker verification",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - Allow all origins in development, restrict in production
cors_origins = os.getenv("CORS_ORIGINS", '["*"]')
if cors_origins == '["*"]':
    allowed_origins = ["*"]
else:
    import json
    allowed_origins = json.loads(cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - routers with their own prefix don't need it here
app.include_router(enroll.router, tags=["enrollment"])  # Has /enroll prefix in router
app.include_router(verify.router, tags=["verification"])  # Has /verify prefix in router
app.include_router(transcribe.router, tags=["transcription"])  # Has /transcribe prefix in router
app.include_router(parse.router, tags=["parsing"])  # Has /parse prefix in router
app.include_router(voice_pay.router, tags=["voice-pay"])  # Has /voice-pay prefix in router
app.include_router(payment_intent.router, tags=["payment-intent"])  # No prefix in router
app.include_router(payment.router, tags=["payment"])  # No prefix in router
app.include_router(challenge.router, tags=["challenge"])  # Has /challenge prefix in router
app.include_router(wallet.router, tags=["wallet"])  # No prefix in router
app.include_router(contacts.router, tags=["contacts"])  # Has /contacts prefix in router
app.include_router(qr.router, tags=["qr"])  # Has /qr prefix in router


@app.get("/", tags=["health"])
@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint for Railway"""
    return {"status": "ok", "service": "VPay"}


@app.get("/debug/db", tags=["debug"])
async def download_database():
    """Download the SQLite database file (debug only)"""
    db_path = "database.db"
    if os.path.exists(db_path):
        return FileResponse(db_path, media_type='application/octet-sqlite', filename="database.db")
    return {"error": "Database not found"}


@app.get("/debug/db/inspect", tags=["debug"])
async def inspect_database():
    """View database contents as JSON"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    result = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        result[table] = [dict(row) for row in rows]

    conn.close()
    return result