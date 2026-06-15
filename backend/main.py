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
try:
    from routes import face_enroll
    print("FACE ROUTER IMPORTED")
except Exception as e:
    print("FACE ROUTER FAILED:", repr(e))
    raise

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
    try:
        from services.ml_warmup import preload_models
        preload_models()
    except Exception as e:
        logger.warning(f"ML model preload failed: {e}. Models will load on first use.")


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

# Include routers
app.include_router(enroll.router, prefix="/enroll", tags=["enrollment"])
app.include_router(face_enroll.router, prefix="/face", tags=["face-verification"])
app.include_router(verify.router, prefix="/verify", tags=["verification"])
app.include_router(transcribe.router, prefix="/transcribe", tags=["transcription"])
app.include_router(parse.router, prefix="/parse", tags=["parsing"])
app.include_router(voice_pay.router, prefix="/voice-pay", tags=["voice-pay"])
app.include_router(payment_intent.router, prefix="/pay/intent", tags=["payment-intent"])
app.include_router(payment.router, prefix="/pay", tags=["payment"])
app.include_router(challenge.router, prefix="/challenge", tags=["challenge"])
app.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
app.include_router(qr.router, prefix="/qr", tags=["qr"])


@app.get("/", tags=["health"])
@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint for Railway"""
    return {"status": "ok", "service": "VPay"}