"""
Environment-driven configuration for VPay.
"""

import os

VERIFY_THRESHOLD = float(os.getenv("VERIFY_THRESHOLD", "0.5"))
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
# Beam size 5 gives noticeably better accuracy for Indian-accented English/Hinglish
# than 1, while still being fast on GPU (and acceptable on CPU).
WHISPER_BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
# Kept at 1 for ultra-fast confirmation, but best_of=2 compensates slightly.
WHISPER_BEAM_SIZE_FAST = int(os.getenv("WHISPER_BEAM_SIZE_FAST", "1"))
# Disabled by default - models load on first request to avoid OOM on Railway
PRELOAD_ML_MODELS = os.getenv("PRELOAD_ML_MODELS", "false").lower() in ("1", "true", "yes")
# Cap decoded audio length to speed up STT (seconds)
MAX_AUDIO_SECONDS_PAY = float(os.getenv("MAX_AUDIO_SECONDS_PAY", "30"))
MAX_AUDIO_SECONDS_CONFIRM = float(os.getenv("MAX_AUDIO_SECONDS_CONFIRM", "12"))
CHALLENGE_TTL_SECONDS = int(os.getenv("CHALLENGE_TTL_SECONDS", "120"))
PARSE_MIN_CONFIDENCE = float(os.getenv("PARSE_MIN_CONFIDENCE", "0.5"))
PHRASE_MATCH_MIN_RATIO = float(os.getenv("PHRASE_MATCH_MIN_RATIO", "0.55"))

# AASIST anti-spoofing threshold (higher = stricter spoof detection)
LIVENESS_THRESHOLD = float(os.getenv("LIVENESS_THRESHOLD", "0.5"))

# One-shot enrollment: chunk duration for splitting long recordings
ENROLLMENT_CHUNK_DURATION_SEC = float(os.getenv("ENROLLMENT_CHUNK_DURATION_SEC", "3.0"))