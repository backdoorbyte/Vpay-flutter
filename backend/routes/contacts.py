"""Saved payee contacts for voice name → UPI resolution."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

import aiosqlite
from database.connection import get_db
from models.schemas import (
    ContactCreateRequest,
    ContactItem,
    ContactListResponse,
)
from services import contact_service
from services.upi_utils import is_valid_upi

router = APIRouter(tags=["Contacts"])

DEFAULT_USER_ID = 1


@router.get("/contacts", response_model=ContactListResponse)
async def get_contacts(db: aiosqlite.Connection = Depends(get_db)):
    rows = await contact_service.list_contacts(db, DEFAULT_USER_ID)
    return ContactListResponse(
        contacts=[ContactItem(**r) for r in rows]
    )


@router.post("/contacts", response_model=ContactItem)
async def create_contact(
    body: ContactCreateRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    upi = body.upi_id.strip().lower()
    if not is_valid_upi(upi):
        raise HTTPException(status_code=400, detail="Invalid UPI ID format")
    row = await contact_service.add_contact(
        db, body.name, upi, body.phone, DEFAULT_USER_ID
    )
    return ContactItem(**row)


@router.delete("/{contact_id}")
async def remove_contact(
    contact_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    ok = await contact_service.delete_contact(db, contact_id, DEFAULT_USER_ID)
    if not ok:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"success": True}
