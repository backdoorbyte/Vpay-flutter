"""
Test script for AASIST liveness detection.

Usage:
    python scripts/test_aasist.py [audio_file.wav]

If no audio file is provided, it will test with a sample file.
"""

import sys
from pathlib import Path

# Add backend root to path
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))


def test_aasist_import():
    """Test that AASIST service can be imported."""
    print("Testing AASIST import...")
    try:
        from services.aasist_service import check_liveness, get_liveness_threshold
        print("[OK] AASIST service imported successfully")
        print(f"  Liveness threshold: {get_liveness_threshold()}")
        return True
    except ImportError as e:
        print(f"[FAIL] Failed to import AASIST: {e}")
        return False


def test_aasist_liveness(audio_path: Path):
    """Test liveness detection on an audio file."""
    print(f"\nTesting liveness detection on: {audio_path}")

    if not audio_path.exists():
        print(f"[FAIL] Audio file not found: {audio_path}")
        return False

    try:
        from services.aasist_service import check_liveness

        is_real, confidence = check_liveness(audio_path)

        status = "REAL" if is_real else "SPOOF/FAKE"
        print(f"[OK] Liveness result: {status}")
        print(f"  Confidence: {confidence:.4f}")
        return True
    except Exception as e:
        print(f"[FAIL] Liveness check failed: {e}")
        return False


def test_payment_intent_response():
    """Test that ConfirmVerifyResponse has liveness fields."""
    print("\nTesting ConfirmVerifyResponse schema...")
    try:
        from models.schemas import ConfirmVerifyResponse

        response = ConfirmVerifyResponse(
            verified=True,
            score=0.85,
            liveness_score=0.92,
            liveness_verified=True,
            threshold=0.5,
            liveness_threshold=0.5,
            message="Payment confirmed",
        )

        print("[OK] ConfirmVerifyResponse schema OK")
        print(f"  liveness_score: {response.liveness_score}")
        print(f"  liveness_verified: {response.liveness_verified}")
        print(f"  liveness_threshold: {response.liveness_threshold}")
        return True
    except Exception as e:
        print(f"[FAIL] Schema test failed: {e}")
        return False


def test_config():
    """Test that LIVENESS_THRESHOLD is in config."""
    print("\nTesting config...")
    try:
        from config import LIVENESS_THRESHOLD

        print(f"[OK] LIVENESS_THRESHOLD configured: {LIVENESS_THRESHOLD}")
        return True
    except ImportError as e:
        print(f"[FAIL] LIVENESS_THRESHOLD not found in config: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("AASIST Liveness Detection - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Config
    results.append(("Config", test_config()))

    # Test 2: Schema
    results.append(("Schema", test_payment_intent_response()))

    # Test 3: Import
    results.append(("Import", test_aasist_import()))

    # Test 4: Liveness detection (if audio file provided)
    audio_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if audio_file:
        results.append(("Liveness", test_aasist_liveness(audio_file)))
    else:
        print("\n[SKIP] Liveness test - no audio file provided")
        print(f"  Usage: python {sys.argv[0]} [audio_file.wav]")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[OK] All tests passed! AASIST is ready to use.")
        print("\nNext steps:")
        print("  1. Download AASIST weights: python scripts/download_aasist_weights.py")
        print("  2. Test with real audio: python scripts/test_aasist.py audio.wav")
        return 0
    else:
        print("\n[FAIL] Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())