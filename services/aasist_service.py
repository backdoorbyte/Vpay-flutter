"""
AASIST anti-spoofing for voice liveness detection.
Model: clovaai/aasist (https://github.com/clovaai/aasist)

Detects:
- Replay attacks (recorded voice played back)
- Synthetic/TTS-generated speech
- Voice conversion attacks
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

_model = None
_device = None
_bonafide_threshold = 0.5  # Tunable: higher = stricter spoof detection
_model_load_failed = False  # Track if model failed to load


def _get_model():
    """Load AASIST once (lazy load)."""
    global _model, _device, _model_load_failed

    if _model_load_failed:
        # Model already failed to load, return sentinel
        logger.warning("AASIST model unavailable, skipping liveness check")
        return None, None

    if _model is not None:
        logger.info("AASIST model already loaded, reusing cached instance")
        return _model, _device

    logger.info("Loading AASIST anti-spoofing model...")

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"AASIST will run on {_device}")

    # Load from pretrained_models/aasist/
    backend_root = Path(__file__).resolve().parents[1]
    aasist_dir = backend_root / "pretrained_models" / "aasist"

    if not aasist_dir.exists():
        logger.error(f"AASIST directory not found: {aasist_dir}")
        _model_load_failed = True
        return None, None

    # Check for required files
    config_path = aasist_dir / "config.json"
    weights_path = aasist_dir / "weights.pt"

    if not config_path.exists():
        logger.error(f"Config not found: {config_path}")
        logger.error("Run: python scripts/download_aasist_weights.py")
        _model_load_failed = True
        return None, None

    if not weights_path.exists():
        logger.error(f"Weights not found: {weights_path}")
        logger.error("Run: python scripts/download_aasist_weights.py")
        _model_load_failed = True
        return None, None

    try:
        # Add models directory to path
        models_dir = aasist_dir / "models"
        import sys
        sys.path.insert(0, str(models_dir))

        # Load config (it's actually JSON format)
        with open(config_path, "r") as f:
            config = json.load(f)

        model_config = config["model_config"]

        # Import and instantiate model
        from AASIST import Model as AASISTModel
        _model = AASISTModel(model_config).to(_device)

        # Load weights
        _model.load_state_dict(torch.load(weights_path, map_location=_device, weights_only=False))
        _model.eval()

        # Count parameters
        nb_params = sum([param.view(-1).size()[0] for param in _model.parameters()])
        logger.info(f"AASIST model loaded successfully ({nb_params:,} parameters)")
        return _model, _device

    except Exception as e:
        logger.error(f"Failed to load AASIST: {e}")
        logger.warning("AASIST liveness detection will be DISABLED until model is fixed")
        import traceback
        logger.debug(traceback.format_exc())
        _model_load_failed = True
        return None, None


def check_liveness(wav_path: Path) -> Tuple[bool, float]:
    """
    Check if audio is from a real human (not spoofed/replayed).

    Args:
        wav_path: Path to 16kHz mono WAV file

    Returns:
        (is_bonafide, confidence_score)
        - is_bonafide: True if real human speech (not spoof)
        - confidence: 0-1 score (higher = more confident it's real)

    Note: If AASIST model is unavailable, returns (True, 1.0) to allow
          payment flow to continue (liveness check skipped).
    """
    model, device = _get_model()

    # Graceful fallback: if model unavailable, assume liveness passed
    # This allows the system to work without AASIST until it's installed
    if model is None:
        logger.warning(f"Liveness check SKIPPED for {wav_path} (model unavailable)")
        return True, 1.0  # Pass through - don't block payments

    # Load audio
    waveform = _load_audio(wav_path)

    # Convert to tensor and add batch dimension
    # AASIST expects input shape [batch, time] - raw waveform
    waveform_tensor = torch.from_numpy(waveform).float().to(device)

    # Ensure proper shape [1, time]
    if waveform_tensor.dim() == 1:
        waveform_tensor = waveform_tensor.unsqueeze(0)

    with torch.no_grad():
        # AASIST returns (last_hidden, output) tuple
        # output is [batch, 2] logits [spoof, bonafide]
        last_hidden, output = model(waveform_tensor)

        # Handle output shape
        if output.dim() == 1:
            output = output.unsqueeze(0)

        # Extract bonafide probability (index 1 = bonafide)
        if output.size(1) == 2:
            # Two-class output: [spoof, bonafide]
            probs = F.softmax(output, dim=1)
            prob_bonafide = probs[0, 1].item()
        else:
            # Single score output (higher = more bonafide)
            prob_bonafide = torch.sigmoid(output[0, 0]).item()

    is_bonafide = prob_bonafide >= _bonafide_threshold

    logger.debug(f"Liveness check: bonafide_prob={prob_bonafide:.4f}, is_bonafide={is_bonafide}")

    return is_bonafide, prob_bonafide


def _load_audio(wav_path: Path) -> np.ndarray:
    """
    Load WAV file as float32 numpy array.
    Handles resampling and stereo-to-mono conversion.
    """
    import soundfile as sf
    import librosa

    data, sr = sf.read(str(wav_path), dtype="float32")

    # Convert stereo to mono if needed
    if data.ndim > 1:
        data = data.mean(axis=1)

    # Resample to 16kHz if needed (AASIST trained on 16kHz)
    if sr != 16000:
        data = librosa.resample(data, orig_sr=sr, target_sr=16000)

    return data


# Constants
SAMPLE_RATE = 16000  # AASIST expects 16kHz


def get_liveness_threshold() -> float:
    """Get current liveness threshold from config."""
    from config import LIVENESS_THRESHOLD
    return LIVENESS_THRESHOLD