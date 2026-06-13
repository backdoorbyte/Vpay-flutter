"""
Bug Condition Exploration Tests — Task 1 (updated for Task 3.6)

Bug manifestation 4: backend passes a non-None language hint to Whisper.

Original bug condition (unfixed code):
  - POST /voice-pay/parse?language=en  → transcribe_audio called with "en"
  - POST /voice-pay/confirm?...&language=hi → transcribe_audio called with "hi"

After fix (tasks 3.3 / 3.4 applied) — expected behavior:
  - transcribe_audio is called with None → auto-detection used
  - Both tests PASS, confirming the fix is in place.

Counterexamples documented (original bugs):
  - transcribe_audio called with language="en" instead of None  (/parse)
  - transcribe_audio called with language="hi" instead of None  (/confirm)

Validates: Requirements 2.3, 2.4
**Validates: Requirements 2.3, 2.4**
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# DB dependency override — avoids needing a real initialized database
# ---------------------------------------------------------------------------

async def _mock_db():
    """Yield a MagicMock in place of a real aiosqlite connection."""
    yield MagicMock()


# ---------------------------------------------------------------------------
# App fixture — import once, override dependencies, keep tests isolated
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a FastAPI TestClient for the VPay app with DB dependency overridden."""
    from main import app
    from database.connection import get_db

    app.dependency_overrides[get_db] = _mock_db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _dummy_audio_file():
    """Return a minimal byte stream that passes UploadFile acceptance."""
    return io.BytesIO(b"\x1a\x45\xdf\xa3" + b"\x00" * 64)


def _make_transcribe_mock(return_text: str = "send 200 to rahul"):
    """Return a regular MagicMock for transcribe_audio → (text, detected_lang)."""
    return MagicMock(return_value=(return_text, "en"))


# ---------------------------------------------------------------------------
# Bug manifestation 4a (FIXED) — /voice-pay/parse calls transcribe_audio
# with None (auto-detect), NOT a language hint.
#
# After fix (task 3.3): transcribe_audio is called with None → test PASSES.
# ---------------------------------------------------------------------------

def test_voice_pay_parse_calls_transcribe_with_none(client):
    """
    POST /voice-pay/parse (no language param) should call transcribe_audio
    with None after the fix — confirming auto-detection is used.

    Expected: transcribe_audio(wav_path, None) — language is None, not "en".

    Bug manifestation 4 (fixed) / Validates: Requirements 2.3, 2.4
    """
    transcribe_mock = _make_transcribe_mock("send 200 to rahul@ybl")

    dummy_path = Path("/tmp/dummy.wav")
    save_mock = AsyncMock(return_value=dummy_path)

    parsed_result = MagicMock()
    parsed_result.amount = 200.0
    parsed_result.upi_id = "rahul@ybl"
    parsed_result.recipient = "rahul"
    parsed_result.confidence = 0.9
    parsed_result.model_copy.return_value = parsed_result

    resolve_mock = AsyncMock(return_value=parsed_result)

    with patch("routes.voice_pay.transcribe_audio", transcribe_mock), \
         patch("routes.voice_pay.save_upload_to_wav", save_mock), \
         patch("routes.voice_pay.parse_and_resolve_text", return_value=parsed_result), \
         patch("routes.voice_pay.resolve_recipient", resolve_mock), \
         patch("routes.voice_pay.cleanup_path"):

        audio_bytes = _dummy_audio_file()
        response = client.post(
            "/voice-pay/parse",
            files={"audio": ("recording.webm", audio_bytes, "audio/webm")},
        )

    # After fix: transcribe_audio IS called with None → assertion passes, confirming fix.
    assert transcribe_mock.called, (
        f"transcribe_audio was never called. Response: {response.status_code} {response.text[:300]}"
    )
    _args, _kwargs = transcribe_mock.call_args
    language_arg = _args[1] if len(_args) > 1 else _kwargs.get("language")

    # Expected: language_arg is None (auto-detection; bug is fixed)
    assert language_arg is None, (
        f"Expected transcribe_audio to be called with None after fix, "
        f"but got: {language_arg!r}"
    )


# ---------------------------------------------------------------------------
# Bug manifestation 4b (FIXED) — /voice-pay/confirm calls transcribe_audio
# with None (auto-detect), NOT a language hint.
#
# After fix (task 3.4): transcribe_audio is called with None → test PASSES.
# ---------------------------------------------------------------------------

def test_voice_pay_confirm_calls_transcribe_with_none(client):
    """
    POST /voice-pay/confirm?intent_id=<id> should call transcribe_audio with
    None after the fix — confirming auto-detection is used for confirmation clips.

    Expected: transcribe_audio(wav_path, None, fast=True) — language is None.

    Bug manifestation 4 (fixed) / Validates: Requirements 2.3, 2.4
    """
    from routes.payment_intent import _new_intent_id, _intents

    # Inject a valid (non-expired, non-used) intent so the endpoint reaches STT.
    intent_id = _new_intent_id()
    _intents[intent_id] = {
        "user_id": 1,
        "recipient": "rahul",
        "upi_id": "rahul@ybl",
        "amount": 200.0,
        "note": "",
        "display_text": "Pay 200 to rahul@ybl",
        "confirm_prompt": "Confirm 200 to rahul@ybl?",
        "expires_at": datetime.utcnow() + timedelta(seconds=300),
        "used": False,
    }

    transcribe_mock = _make_transcribe_mock("yes confirm the payment")
    dummy_path = Path("/tmp/dummy.wav")
    save_mock = AsyncMock(return_value=dummy_path)

    import numpy as np

    with patch("routes.payment_intent.transcribe_audio", transcribe_mock), \
         patch("routes.payment_intent.save_upload_to_wav", save_mock), \
         patch("routes.payment_intent.cleanup_path"), \
         patch("routes.payment_intent.enrollment_service") as enroll_mock, \
         patch("routes.payment_intent.verify_against_enrolled", return_value=(True, 0.95)):

        enroll_mock.get_enrolled_embedding = AsyncMock(return_value=np.zeros(192))

        audio_bytes = _dummy_audio_file()
        response = client.post(
            f"/voice-pay/confirm?intent_id={intent_id}",
            files={"audio": ("recording.webm", audio_bytes, "audio/webm")},
        )

    # After fix: transcribe_audio IS called with None → assertion passes, confirming fix.
    assert transcribe_mock.called, (
        f"transcribe_audio was never called. Response: {response.status_code} {response.text[:300]}"
    )
    _args, _kwargs = transcribe_mock.call_args
    language_arg = _args[1] if len(_args) > 1 else _kwargs.get("language")

    # Expected: language_arg is None (auto-detection; bug is fixed)
    assert language_arg is None, (
        f"Expected transcribe_audio to be called with None after fix, "
        f"but got: {language_arg!r}"
    )
