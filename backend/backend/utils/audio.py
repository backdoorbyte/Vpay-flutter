"""
Audio ingestion utilities: decode uploads to mono 16 kHz WAV for ML pipelines.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf
from fastapi import UploadFile
import librosa

logger = logging.getLogger("vpay")

SAMPLE_RATE = 16000

# File extensions that need ffmpeg decoding
_FFMPEG_EXTS = {".webm", "ogg", "ogg", ".mp4", ".m4a", ".mp3", ".aac"}


def _needs_ffmpeg(suffix: str) -> bool:
    return suffix.lower() in _FFMPEG_EXTS


def _convert_with_ffmpeg(input_path: Path, output_wav: Path) -> None:
    """Use ffmpeg to convert any format to 16 kHz mono WAV."""
    cmd = [
        "ffmpeg",
        "-y",  # overwrite output
        "-i", str(input_path),
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
        "-acodec", "pcm_s16le",
        str(output_wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")


def _trim_audio(y, max_seconds: float | None):
    """Limit length so STT/speaker models process less audio."""
    if max_seconds is None or max_seconds <= 0:
        return y
    max_samples = int(max_seconds * SAMPLE_RATE)
    if len(y) > max_samples:
        return y[:max_samples]
    return y


async def save_upload_to_wav(
    upload: UploadFile,
    *,
    max_seconds: float | None = None,
) -> Path:
    """
    Persist uploaded audio to a temp WAV file at 16 kHz mono.

    Supports webm/wav/ogg/mp4 from browser MediaRecorder.
    Uses ffmpeg for webm/ogg/mp4 formats, librosa for wav.
    """
    raw = await upload.read()
    suffix = Path(upload.filename or "audio.webm").suffix or ".webm"
    temp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_in.write(raw)
    temp_in.close()

    backend_root = Path(__file__).resolve().parents[1]
    out_dir = backend_root / "tmp_audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"tmp_{uuid.uuid4().hex}.wav"

    try:
        if _needs_ffmpeg(suffix):
            # ffmpeg is required for webm/ogg/mp4/etc.
            _convert_with_ffmpeg(Path(temp_in.name), out_path)
            # Apply trimming if needed
            if max_seconds is not None and max_seconds > 0:
                data, sr = sf.read(str(out_path), dtype="float32")
                if data.ndim > 1:
                    data = data.mean(axis=1)
                max_samples = int(max_seconds * SAMPLE_RATE)
                if len(data) > max_samples:
                    sf.write(str(out_path), data[:max_samples], sr)
        else:
            # Direct read for wav/aiff/flac etc.
            try:
                y, sr = sf.read(temp_in.name, dtype="float32")
            except sf.LibsndfileError:
                # Fallback: librosa
                y, sr = librosa.load(temp_in.name, sr=SAMPLE_RATE, mono=True)
            else:
                if y.ndim > 1:
                    y = y.mean(axis=1)
                if sr != SAMPLE_RATE:
                    y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
            y = _trim_audio(y, max_seconds)
            sf.write(str(out_path), y, SAMPLE_RATE)
    finally:
        Path(temp_in.name).unlink(missing_ok=True)

    return out_path


def wav_to_tensor(wav_path: Path) -> Tuple[np.ndarray, int]:
    """Load WAV as float32 numpy array."""
    data, sr = sf.read(str(wav_path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, sr


def cleanup_path(path: Path) -> None:
    """Remove temporary file if it exists."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def chunk_audio(wav_path: Path, chunk_duration_sec: float = 3.0) -> list[Path]:
    """
    Split a long audio file into multiple chunks of fixed duration.

    Args:
        wav_path: Path to the input WAV file (16 kHz mono)
        chunk_duration_sec: Duration of each chunk in seconds

    Returns:
        List of paths to chunked WAV files
    """
    data, sr = sf.read(str(wav_path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)

    chunk_samples = int(chunk_duration_sec * sr)
    chunks = []

    backend_root = Path(__file__).resolve().parents[1]
    out_dir = backend_root / "tmp_audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(0, len(data), chunk_samples):
        chunk_data = data[i : i + chunk_samples]
        # Skip very short chunks (less than 1 second)
        if len(chunk_data) < sr:
            continue

        chunk_path = out_dir / f"chunk_{uuid.uuid4().hex}.wav"
        sf.write(str(chunk_path), chunk_data, sr)
        chunks.append(chunk_path)

    logger.info(f"Chunked audio into {len(chunks)} chunks (chunk_duration={chunk_duration_sec}s)")
    return chunks
