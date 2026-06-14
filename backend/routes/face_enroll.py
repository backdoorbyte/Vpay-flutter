"""
Face enrollment and verification routes.
"""

from __future__ import annotations

import logging
from pathlib import Path
import aiosqlite
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from database.connection import get_db
from models.schemas import EnrollResponse
from services import face_verification_service
from utils.audio import cleanup_path, save_upload_to_wav

router = APIRouter(tags=["Face Verification"])
logger = logging.getLogger("vpay")

DEFAULT_USER_ID = 1


@router.post("/enroll", response_model=EnrollResponse)
async def enroll_face(
    image: UploadFile = File(..., description="Face image for enrollment"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Enroll user's face for verification."""
    temp_path: Path | None = None
    try:
        # Save image temporarily
        temp_path = Path(f"tmp_audio/face_{DEFAULT_USER_ID}.jpg")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        content = await image.read()

        # Validate image content
        if not content or len(content) < 1024:
            logger.error(f"Invalid image content: {len(content)} bytes")
            return EnrollResponse(
                success=False,
                message="Invalid image: file too small or empty",
                samples_received=0,
                samples_required=1,
                enrolled=False,
            )

        temp_path.write_bytes(content)
        logger.info(f"Saved face image to {temp_path} ({len(content)} bytes)")

        success, message = await face_verification_service.enroll_face(DEFAULT_USER_ID, temp_path)
        logger.info(f"Face enrollment result: success={success}, message={message}")

        if success:
            # Persist to DB
            embedding = face_verification_service.get_cached_embedding(DEFAULT_USER_ID)
            if embedding:
                await db.execute(
                    """
                    INSERT INTO face_embeddings (user_id, embedding_json)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET embedding_json = ?, enrolled_at = datetime('now')
                    """,
                    (DEFAULT_USER_ID, str(embedding), str(embedding)),
                )
                await db.execute(
                    "UPDATE users SET is_face_enrolled = 1 WHERE id = ?",
                    (DEFAULT_USER_ID,),
                )
                await db.commit()
                logger.info(f"Face enrollment persisted to DB for user {DEFAULT_USER_ID}")

            return EnrollResponse(
                success=True,
                message=message,
                samples_received=1,
                samples_required=1,
                enrolled=True,
            )
        else:
            return EnrollResponse(
                success=False,
                message=message,
                samples_received=0,
                samples_required=1,
                enrolled=False,
            )
    except Exception as e:
        logger.error(f"Face enrollment error: {e}", exc_info=True)
        return EnrollResponse(
            success=False,
            message=str(e),
            samples_received=0,
            samples_required=1,
            enrolled=False,
        )
    finally:
        if temp_path:
            cleanup_path(temp_path)


@router.post("/verify")
async def verify_face(
    image: UploadFile = File(..., description="Face image for verification"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Verify user's face against enrolled embedding."""
    temp_path: Path | None = None
    try:
        # Load enrolled embedding from DB if not in cache
        cursor = await db.execute(
            "SELECT embedding_json FROM face_embeddings WHERE user_id = ?",
            (DEFAULT_USER_ID,),
        )
        row = await cursor.fetchone()
        if row and row[0]:
            import ast
            embedding = ast.literal_eval(row[0])
            face_verification_service.load_embedding(DEFAULT_USER_ID, embedding)

        # Save probe image
        temp_path = Path(f"tmp_audio/verify_{DEFAULT_USER_ID}.jpg")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        content = await image.read()
        temp_path.write_bytes(content)

        is_match, confidence, message = await face_verification_service.verify_face(
            DEFAULT_USER_ID, temp_path, threshold=0.6
        )

        return {
            "verified": is_match,
            "confidence": confidence,
            "message": message,
        }
    except Exception as e:
        logger.error(f"Face verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path:
            cleanup_path(temp_path)


@router.get("/status")
async def face_enrollment_status(db: aiosqlite.Connection = Depends(get_db)):
    """Check if user has enrolled face."""
    cursor = await db.execute(
        "SELECT is_face_enrolled FROM users WHERE id = ?",
        (DEFAULT_USER_ID,),
    )
    row = await cursor.fetchone()
    is_enrolled = bool(row and row[0])

    return {
        "is_face_enrolled": is_enrolled,
    }


@router.delete("/reset")
async def reset_face_enrollment(db: aiosqlite.Connection = Depends(get_db)):
    """Clear face enrollment data."""
    face_verification_service.clear_embedding(DEFAULT_USER_ID)
    await db.execute("DELETE FROM face_embeddings WHERE user_id = ?", (DEFAULT_USER_ID,))
    await db.execute("UPDATE users SET is_face_enrolled = 0 WHERE id = ?", (DEFAULT_USER_ID,))
    await db.commit()
    return {"success": True, "message": "Face enrollment reset"}