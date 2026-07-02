"""
Preservation Property Tests — Task 2 (Backend)

Property 2: Preservation — Non-Recording-Language Behaviors Are Unchanged.

These tests document BASELINE behaviors that must be preserved after the fix.
They target code paths that are NOT being changed and must pass on unfixed code.

Expected outcomes on UNFIXED code:
  P2e — ("en","en"), ("hi","hi"), ("hinglish",None) PASS.
        ("None",None) MAY FAIL if the None guard is not yet added.
  P2f — MAY FAIL if transcribe_audio default is still "en" (not None).
        This is expected and documented below.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Ensure backend root is on sys.path so imports work the same as in production.
# ---------------------------------------------------------------------------

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


# ---------------------------------------------------------------------------
# P2e — _language_hint unit test
#
# Parameterise over the full mapping table.
# On unfixed code:
#   ("en","en")           → PASSES  (mapping present)
#   ("hi","hi")           → PASSES  (mapping present)
#   ("hinglish", None)    → PASSES  (mapping falls back to None via .get)
#   (None, None)          → MAY FAIL if no None guard exists yet
#
# All four must PASS after the fix (task 3.5 adds the None guard).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "lang_input, expected",
    [
        ("en", "en"),        # P2e-1: known language → passes through unchanged
        ("hi", "hi"),        # P2e-2: known language → passes through unchanged
        ("hinglish", None),  # P2e-3: hinglish → None (auto-detect; already returns None)
        (None, None),        # P2e-4: None input → None (requires None guard from task 3.5)
    ],
    ids=["en→en", "hi→hi", "hinglish→None", "None→None"],
)
def test_language_hint_mapping(lang_input: Optional[str], expected: Optional[str]):
    """
    _language_hint must map known language codes correctly and return None for
    unknown or None inputs.

    P2e-1, P2e-2, P2e-3 PASS on unfixed code.
    P2e-4 MAY FAIL on unfixed code if the None guard is absent — that is expected.

    Validates: Requirements 3.4, 3.5
    """
    from services.whisper_service import _language_hint

    result = _language_hint(lang_input)
    assert result == expected, (
        f"_language_hint({lang_input!r}) returned {result!r}, expected {expected!r}"
    )


# ---------------------------------------------------------------------------
# P2f — transcribe_audio with explicit None calls Whisper with language=None
#
# After the fix (task 3.5):
#   - transcribe_audio signature changes default to language=None
#   - _language_hint(None) returns None
#   - model.transcribe is called with language=None
#
# On unfixed code this test MAY FAIL because:
#   - language default is "en" (but we pass None explicitly, so that's fine)
#   - _language_hint(None) may raise or return an unexpected value
#
# The explicit call transcribe_audio(path, None) is what we test here.
# ---------------------------------------------------------------------------

def test_transcribe_audio_with_explicit_none_calls_whisper_with_none():
    """
    transcribe_audio(path, None) must call model.transcribe with language=None
    so Whisper performs auto-detection.

    On unfixed code this test MAY FAIL if transcribe_audio default is "en" and
    _language_hint(None) doesn't handle None — documented expected failure.
    After fix (task 3.5): _language_hint(None) returns None, default is None
    → model.transcribe called with language=None → test PASSES.

    Validates: Requirements 3.4
    """
    import services.whisper_service as ws_module

    # Build a minimal mock model that returns the shape Whisper produces.
    mock_segment = MagicMock()
    mock_segment.text = "hello world"

    mock_info = MagicMock()
    mock_info.language = "en"

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    # Patch both _get_model (to inject our mock) and the module-level _model
    # so the real WhisperModel is never loaded.
    with patch.object(ws_module, "_get_model", return_value=mock_model):
        # Pass explicit None — this is the post-fix call we're documenting
        result_text, result_lang = ws_module.transcribe_audio(Path("/tmp/dummy.wav"), None)

    # The model.transcribe call must have language=None
    assert mock_model.transcribe.called, "model.transcribe was never called"
    _, call_kwargs = mock_model.transcribe.call_args
    assert call_kwargs.get("language") is None, (
        f"Expected model.transcribe to be called with language=None, "
        f"but got language={call_kwargs.get('language')!r}"
    )

    # Also verify the response shape is preserved (TranscribeResponse contract)
    assert isinstance(result_text, str)
    assert isinstance(result_lang, str)


# ---------------------------------------------------------------------------
# P2e-extended — unknown string input returns None (mapping fallback)
#
# This verifies the dict.get(..., None) fallback for arbitrary unknown strings.
# PASSES on unfixed code (the .get fallback already returns None).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "unknown_lang",
    ["fr", "de", "zh", "unknown", "", "ENGLISH"],
    ids=lambda x: f"unknown({x!r})",
)
def test_language_hint_unknown_strings_return_none(unknown_lang: str):
    """
    _language_hint(x) must return None for any string not in {"en", "hi"}.
    This is the existing dict.get fallback behaviour — must be preserved.

    PASSES on unfixed code.
    Validates: Requirements 3.4
    """
    from services.whisper_service import _language_hint

    result = _language_hint(unknown_lang)
    assert result is None, (
        f"_language_hint({unknown_lang!r}) returned {result!r}, expected None"
    )
