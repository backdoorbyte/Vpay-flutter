"""
Pydantic request/response models for OpenAPI documentation.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class LanguageCode(str, Enum):
    en = "en"
    hi = "hi"
    hinglish = "hinglish"


class EnrollResponse(BaseModel):
    success: bool
    message: str
    samples_received: int
    samples_required: int = 20
    enrolled: bool = False


class VerifyResponse(BaseModel):
    verified: bool
    score: float = Field(..., description="Cosine similarity 0-1")
    threshold: float
    message: str


class TranscribeResponse(BaseModel):
    text: str
    language: str


class ParsedCommand(BaseModel):
    recipient: Optional[str] = None
    upi_id: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None
    raw_text: str
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    resolution: str = Field(
        "unknown",
        description="spoken_upi | contact | contact_phone | spoken_phone | unresolved",
    )


class ChallengeResponse(BaseModel):
    challenge_id: int
    phrase: str
    expires_in_seconds: int


class PaymentRequest(BaseModel):
    recipient: str
    upi_id: str = Field(..., description="Resolved payee UPI VPA")
    amount: float = Field(..., gt=0)
    note: Optional[str] = None
    challenge_id: Optional[int] = None
    intent_id: Optional[int] = None
    verification_score: float


class ContactItem(BaseModel):
    id: int
    name: str
    upi_id: str
    phone: Optional[str] = None


class ContactListResponse(BaseModel):
    contacts: List[ContactItem]


class ContactCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    upi_id: str = Field(..., min_length=3)
    phone: Optional[str] = None


class PaymentResponse(BaseModel):
    success: bool
    message: str
    new_balance: float
    transaction_id: Optional[int] = None


class WalletResponse(BaseModel):
    balance: float
    is_voice_enrolled: bool
    user_name: str


class TransactionItem(BaseModel):
    id: int
    recipient: str
    upi_id: Optional[str] = None
    amount: float
    note: Optional[str]
    status: str
    verification_score: Optional[float]
    created_at: str


class TransactionListResponse(BaseModel):
    transactions: List[TransactionItem]


class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1)


class EnrollStatusResponse(BaseModel):
    samples_received: int
    samples_required: int
    is_voice_enrolled: bool
    pending_in_session: bool


class ChallengeVerifyResponse(BaseModel):
    verified: bool
    score: float
    phrase_match_score: float
    transcribed_text: str = ""
    threshold: float
    limit: float = 0.0
    refined: bool = False
    message: str


class VoicePayResponse(BaseModel):
    transcribed_text: str
    display_text: str = ""
    confirm_prompt: str = ""
    language: str
    parsed: ParsedCommand
    needs_upi: bool = False


class PaymentIntentRequest(BaseModel):
    recipient: str
    upi_id: str
    amount: float = Field(..., gt=0)
    note: Optional[str] = None
    display_text: Optional[str] = None
    confirm_prompt: Optional[str] = None
    language: str = "en"


class PaymentIntentResponse(BaseModel):
    intent_id: int
    display_text: str
    confirm_prompt: str
    expires_in_seconds: int
    language: str = "en"


class ConfirmVerifyResponse(BaseModel):
    verified: bool
    score: float
    liveness_score: float = Field(default=0.0, description="AASIST bonafide probability (0-1)")
    liveness_verified: bool = Field(default=False, description="Did liveness check pass?")
    threshold: float
    liveness_threshold: float = Field(default=0.5, description="AASIST liveness threshold")
    limit: float = 0.0
    refined: bool = False
    transcribed_text: str = ""
    message: str
    payment_completed: bool = False
    new_balance: Optional[float] = None
    transaction_id: Optional[int] = None
    response_text: str = Field(default="", description="Text the frontend should speak to the user after confirmation")
    language: str = "en"


class QrParseResponse(BaseModel):
    upi_id: str = Field(..., description="Receiver UPI ID (pa)")
    payee_name: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    note: Optional[str] = None
    raw_payload: str
