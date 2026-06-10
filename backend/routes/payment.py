"""
POST /pay — mock payment after voice confirmation + speaker verification.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite
from config import VERIFY_THRESHOLD
from database.connection import get_db
from models.schemas import PaymentRequest, PaymentResponse
from routes import challenge as challenge_routes
from routes import payment_intent as intent_routes
from services import challenge_service, payment_service
from services.speaker_service import get_threshold
from services.upi_utils import is_valid_upi

router = APIRouter(tags=["Payments"])

DEFAULT_USER_ID = 1


@router.post("/", response_model=PaymentResponse)
async def pay(
    body: PaymentRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Deduct wallet balance after successful voice confirmation."""
    if body.verification_score < VERIFY_THRESHOLD:
        raise HTTPException(
            status_code=403,
            detail=f"Verification score below threshold ({get_threshold()})",
        )

    if not body.intent_id and not body.challenge_id:
        raise HTTPException(status_code=400, detail="Missing payment intent or challenge")

    if body.intent_id:
        if not intent_routes.is_intent_verified(body.intent_id):
            raise HTTPException(
                status_code=403,
                detail="Complete voice payment confirmation first",
            )
        stored_score = intent_routes.pop_verified_score(body.intent_id)
        intent = intent_routes.get_intent(body.intent_id)
        if stored_score is None or intent is None:
            raise HTTPException(status_code=403, detail="Confirmation expired")
        if intent["used"]:
            raise HTTPException(status_code=403, detail="Payment session already used")
        intent_routes.mark_intent_used(body.intent_id)
    else:
        if not challenge_routes.is_challenge_verified(body.challenge_id):
            raise HTTPException(
                status_code=403,
                detail="Complete challenge voice verification first",
            )
        stored_score = challenge_routes.pop_verified_score(body.challenge_id)
        if stored_score is None:
            raise HTTPException(status_code=403, detail="Challenge verification expired")
        
        # Dynamic limit removed — all verified payments are allowed

        ok, expected_phrase = await challenge_service.validate_challenge(
            db, body.challenge_id, DEFAULT_USER_ID
        )
        if not ok:
            raise HTTPException(status_code=400, detail=expected_phrase)

    if not is_valid_upi(body.upi_id):
        raise HTTPException(status_code=400, detail="Invalid UPI ID")

    success, message, new_balance, tx_id = await payment_service.process_payment(
        db,
        DEFAULT_USER_ID,
        body.recipient,
        body.upi_id.lower(),
        body.amount,
        body.note,
        body.verification_score,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return PaymentResponse(
        success=True,
        message=message,
        new_balance=new_balance,
        transaction_id=tx_id,
    )
