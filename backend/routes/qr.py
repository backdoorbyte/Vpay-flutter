"""
POST /qr/parse — upload payment QR image and extract UPI payee ID.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import QrParseResponse
from services.qr_service import parse_qr_image

router = APIRouter(tags=["QR Payments"])


@router.post("/qr/parse", response_model=QrParseResponse)
async def parse_payment_qr(
    image: UploadFile = File(..., description="UPI payment QR image (PNG/JPEG)"),
):
    """Decode QR from image and return receiver UPI ID and optional amount."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload a PNG or JPEG image.")

    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        parsed = parse_qr_image(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read QR: {e}") from e

    return QrParseResponse(**parsed)
