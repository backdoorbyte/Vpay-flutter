"""
Voice Payment Anti-Spoofing - Fine-tuned AASIST Inference (Fixed)
==================================================================

This module loads your finetuned AASIST model and provides voice
liveness detection for the VPay payment flow.

Fixes applied:
1. Strip 'module.' prefix from DataParallel checkpoints
2. Configurable model path via environment variable
3. Relative imports for integration with vpay-flutter

Usage:
    from services.aasist_inference import LivenessVerifier
    verifier = LivenessVerifier()
    is_authentic, score, verdict = verifier.check_audio("audio.wav")
"""

import os
import sys
from pathlib import Path
import logging

import torch
import numpy as np
import soundfile as sf
import librosa

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ============================================================
# IMPORT MODEL ARCHITECTURE
# ============================================================

# Add models/aasist to Python path for AASIST import
PROJECT_ROOT = Path(__file__).resolve().parents[1]
AASIST_MODEL_DIR = PROJECT_ROOT / "models" / "aasist"

if str(AASIST_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(AASIST_MODEL_DIR))

try:
    from AASIST import Model  # Model architecture from models/aasist/AASIST.py
    logger.info("AASIST model architecture loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import AASIST model: {e}")
    raise


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MODEL_PATH = "pretrained_models/best_aasist_hinglish.pth"


def get_model_config():
    """Return the model configuration used during finetuning."""
    return {
        "architecture": "AASIST",
        "nb_samp": 64600,
        "first_conv": 128,
        "filts": [70, [1, 32], [32, 32], [32, 64], [64, 64]],
        "gat_dims": [64, 32],
        "pool_ratios": [0.5, 0.7, 0.5, 0.5],
        "temperatures": [2.0, 2.0, 100.0, 100.0],
    }


# ============================================================
# AUDIO PREPROCESSING
# ============================================================

def pad_audio(x: np.ndarray, max_len: int = 64600) -> np.ndarray:
    """Pad or trim audio to target length (same as training)."""
    if len(x) >= max_len:
        return x[:max_len]
    repeats = int(max_len / len(x)) + 1
    return np.tile(x, repeats)[:max_len]


def load_audio_for_inference(audio_path: str, max_len: int = 64600) -> np.ndarray:
    """
    Load and preprocess audio file for inference.

    Args:
        audio_path: Path to .wav file
        max_len: Target length in samples (default 64600 = ~4s @ 16kHz)

    Returns:
        Preprocessed audio waveform as numpy array
    """
    try:
        # Load audio (soundfile preserves original sample rate)
        audio, sr = sf.read(audio_path)

        # Convert to mono if stereo
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Resample to 16kHz if needed
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            sr = 16000

        # Pad or trim to target length
        audio = pad_audio(audio, max_len)

        logger.info(
            f"Loaded audio: {len(audio)} samples ({len(audio) / 16000:.2f}s original)"
        )
        return audio

    except Exception as e:
        raise ValueError(f"Failed to load audio file {audio_path}: {e}")


# ============================================================
# LIVENESS VERIFIER CLASS
# ============================================================

class LivenessVerifier:
    """
    Anti-spoofing / liveness verifier for voice-based payments.

    Detects:
    - Replay attacks (recorded speech played back)
    - Voice conversion attacks (synthetic/generated speech)

    Usage:
        >>> verifier = LivenessVerifier()
        >>> is_bonafide, score, verdict = verifier.check_audio("user.wav")
        >>> if is_bonafide:
        ...     print("Payment authorized")
        >>> else:
        ...     print("SPOOF DETECTED - Transaction blocked")
    """

    def __init__(
        self,
        model_path: str = None,
        device: str = None,
        threshold: float = 0.5,
    ):
        """
        Initialize the liveness verifier.

        Args:
            model_path: Path to fine-tuned AASIST checkpoint.
                        Defaults to env var AASIST_MODEL_PATH or pretrained_models/best_aasist_hinglish.pth
            device: "cuda" or "cpu" (auto-detected if None)
            threshold: Decision threshold (default 0.5)
                       Higher = stricter (fewer false accepts)
        """
        # Resolve model path
        if model_path is None:
            model_path = os.getenv("AASIST_MODEL_PATH", DEFAULT_MODEL_PATH)

        self.model_path = model_path
        self.threshold = threshold

        # Setup device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"LivenessVerifier device: {self.device}")

        # Load model
        self.model = self._load_model()

        logger.info(
            f"LivenessVerifier ready | model: {self.model_path} | threshold: {self.threshold}"
        )

    def _strip_module_prefix(self, state_dict: dict) -> dict:
        """
        Strip 'module.' prefix from state_dict keys.
        This happens when model was saved from a DataParallel wrapper.
        """
        new_state_dict = {}
        for key, value in state_dict.items():
            if key.startswith("module."):
                new_key = key[len("module.") :]
            else:
                new_key = key
            new_state_dict[new_key] = value
        return new_state_dict

    def _load_model(self) -> torch.nn.Module:
        """Load and initialize the fine-tuned AASIST model."""

        # Create model with finetuning config
        model_config = get_model_config()
        model = Model(model_config)

        # Resolve absolute path
        checkpoint_path = Path(self.model_path)
        if not checkpoint_path.is_absolute():
            # Relative to project root
            checkpoint_path = PROJECT_ROOT / self.model_path

        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Model checkpoint not found: {checkpoint_path}\n"
                f"Place 'best_aasist_hinglish.pth' in pretrained_models/ or set AASIST_MODEL_PATH"
            )

        # Load checkpoint with security (weights_only=True)
        checkpoint = torch.load(
            str(checkpoint_path),
            map_location=self.device,
            weights_only=True,
        )

        # Extract state dict
        if isinstance(checkpoint, dict):
            if "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
            elif "net" in checkpoint:
                state_dict = checkpoint["net"]
            elif "model" in checkpoint:
                state_dict = checkpoint["model"]
            elif "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint
        else:
            state_dict = checkpoint

        # Strip 'module.' prefix (from DataParallel training)
        state_dict = self._strip_module_prefix(state_dict)

        # Load weights (strict=True, fallback to loose if needed)
        try:
            model.load_state_dict(state_dict, strict=True)
            logger.info("Model weights loaded successfully (strict)")
        except RuntimeError as e:
            logger.warning(f"Strict load failed, trying loose load: {e}")
            model.load_state_dict(state_dict, strict=False)
            logger.info("Model weights loaded ( loose)")

        # Move to device and eval mode
        model.to(self.device)
        model.eval()

        return model

    def check_audio(self, audio_path: str) -> tuple:
        """
        Verify a single audio file for spoof attacks.

        Args:
            audio_path: Path to the audio file to verify

        Returns:
            Tuple of (is_bonafide, confidence, verdict)
            - is_bonafide: True if audio appears to be genuine human speech
            - confidence: Probability score (0-1), higher = more confident it's real
            - verdict: Human-readable verdict string

        Example:
            >>> verifier = LivenessVerifier()
            >>> ok, score, text = verifier.check_audio("payment.wav")
            >>> print(f"Verdict: {text} (score: {score:.2%})")
        """
        # Load and preprocess audio
        audio = load_audio_for_inference(audio_path)

        # Convert to tensor: (batch=1, samples=64600)
        audio_tensor = torch.FloatTensor(audio).unsqueeze(0).to(self.device)

        # Run inference
        with torch.no_grad():
            _, logits = self.model(audio_tensor)

            # Get bonafide probability (class 1)
            probs = torch.softmax(logits, dim=1)
            bonafide_prob = probs[:, 1].item()

        # Decision
        is_bonafide = bonafide_prob >= self.threshold

        # Verdict string
        if bonafide_prob >= 0.8:
            verdict = "AUTHENTIC - High confidence genuine speech"
        elif bonafide_prob >= self.threshold:
            verdict = f"AUTHENTIC - Genuine speech (prob: {bonafide_prob:.2%})"
        elif bonafide_prob >= 0.3:
            verdict = f"SUSPICIOUS - Possible spoof attack (prob: {bonafide_prob:.2%})"
        else:
            verdict = f"SPOOF DETECTED - Likely fake/replayed audio (prob: {bonafide_prob:.2%})"

        return is_bonafide, bonafide_prob, verdict

    def check_batch(self, audio_paths: list) -> list:
        """
        Verify multiple audio files.

        Args:
            audio_paths: List of paths to audio files

        Returns:
            List of dicts with keys: file, is_bonafide, confidence, verdict, error
        """
        results = []
        for audio_path in audio_paths:
            try:
                is_bonafide, conf, verdict = self.check_audio(audio_path)
                results.append(
                    {
                        "file": audio_path,
                        "is_bonafide": is_bonafide,
                        "confidence": conf,
                        "verdict": verdict,
                        "error": None,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "file": audio_path,
                        "is_bonafide": None,
                        "confidence": None,
                        "verdict": None,
                        "error": str(e),
                    }
                )
        return results

    def set_threshold(self, threshold: float):
        """Set decision threshold (0-1)."""
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = threshold
        logger.info(f"Liveness threshold set to: {threshold}")


# ============================================================
# BACKWARD COMPATIBILITY (for existing code)
# ============================================================

class VoicePaymentVerifier(LivenessVerifier):
    """
    Legacy alias for LivenessVerifier.
    Maintains backward compatibility with voice_payment_inference.py usage.
    """

    def __init__(self, model_path: str = None, device: str = None, decision_threshold: float = 0.5):
        super().__init__(model_path=model_path, device=device, threshold=decision_threshold)


# ============================================================
# COMMAND LINE TESTING
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Voice Payment Liveness Detection")
    parser.add_argument("--audio", "-a", type=str, help="Path to single audio file")
    parser.add_argument("--model", "-m", type=str, help="Path to model checkpoint")
    parser.add_argument("--threshold", "-t", type=float, default=0.5, help="Decision threshold")
    parser.add_argument("--device", "-d", type=str, choices=["cuda", "cpu"], help="Device")

    args = parser.parse_args()

    verifier = LivenessVerifier(
        model_path=args.model,
        device=args.device,
        threshold=args.threshold,
    )

    if args.audio:
        is_bonafide, conf, verdict = verifier.check_audio(args.audio)
        print(f"\n{'='*50}")
        print(f"Result: {verdict}")
        print(f"Bonafide: {is_bonafide} (score: {conf:.4f})")
        print(f"{'='*50}")
    else:
        print("Use --audio <path> to verify an audio file")
