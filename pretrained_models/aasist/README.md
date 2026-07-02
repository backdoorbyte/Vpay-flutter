# AASIST Voice Liveness Detection

This directory contains the AASIST (Audio Anti-Spoofing using Integrated Spectro-Temporal Graph) model for voice liveness detection.

## What is AASIST?

AASIST is a state-of-the-art anti-spoofing model that detects:
- **Replay attacks** - Recorded voice played back through a speaker
- **Synthetic speech** - TTS-generated audio (Google TTS, Amazon Polly, etc.)
- **Voice conversion** - Transformed voice attacks

## Setup

### Option 1: Auto-download (Recommended)

Run the download script:

```bash
cd c:\Users\harsh\Documents\vpay-flutter
python scripts/download_aasist_weights.py
```

This will download:
- `config.yaml` - Model configuration
- `weights.pt` - Pretrained weights
- `models/*.py` - Model architecture code

### Option 2: Manual Download

1. Clone the AASIST repository:
   ```bash
   git clone https://github.com/clovaai/aasist.git
   ```

2. Copy the following files to this directory:
   - `config.yaml`
   - `weights.pt` (download from https://huggingface.co/clovaai/aasist)
   - `models/AASIST.py`
   - `models/RawNetBasicBlock.py`
   - `models/__init__.py`

### Required Dependencies

```bash
pip install transformers>=4.35.0 torch torchaudio
```

## Configuration

Edit `LIVENESS_THRESHOLD` in `config.py` or set the environment variable:

```bash
# Higher = stricter (rejects more spoofs, but may reject real users)
# Lower = more permissive (allows more through)
LIVENESS_THRESHOLD=0.5  # Default
```

Recommended values:
- `0.3-0.4` - Permissive (development/testing)
- `0.5-0.6` - Balanced (production default)
- `0.7-0.8` - Strict (high-security environments)

## Usage

The liveness check is automatically called in the `/pay/intent/confirm` endpoint.

To test standalone:

```python
from services.aasist_service import check_liveness
from pathlib import Path

is_real, confidence = check_liveness(Path("audio.wav"))
print(f"Liveness: {'REAL' if is_real else 'SPOOF'} (confidence: {confidence:.2f})")
```

## API Response

The `/pay/intent/confirm` endpoint now returns:

```json
{
  "verified": true,
  "score": 0.85,
  "liveness_score": 0.92,
  "liveness_verified": true,
  "threshold": 0.5,
  "liveness_threshold": 0.5,
  ...
}
```

## Troubleshooting

### Model not loading

1. Ensure weights are downloaded: `ls pretrained_models/aasist/`
2. Check file sizes: `weights.pt` should be ~50MB
3. Verify Python can import: `python -c "from services.aasist_service import check_liveness"`

### Out of memory

AASIST adds ~50-100MB memory footprint. If running on Railway or similar:
- Enable `PRELOAD_ML_MODELS=true` to load at boot
- Ensure sufficient memory allocation (512MB+)

### False positives (real voice rejected)

Lower the threshold:
```bash
LIVENESS_THRESHOLD=0.4
```

### False negatives (spoof accepted)

Raise the threshold:
```bash
LIVENESS_THRESHOLD=0.7
```

## References

- GitHub: https://github.com/clovaai/aasist
- Paper: https://arxiv.org/abs/2109.04191
- HuggingFace: https://huggingface.co/clovaai/aasist