# 🔊 VPay - Voice-Based Payment Authentication

[![Open in HF Spaces](https://huggingface.co/datasets/huggingface/badges/raw/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/YOUR_USERNAME/vpay-backend)

A FastAPI backend for voice-based payment authentication using anti-spoofing (AASIST), speaker verification (ECAPA-TDNN), and speech recognition (Whisper).

## 🌟 Features

- 📄‍☠️ **Anti-Spoofing** (AASIST model) - Detects replay & voice conversion attacks
- 🗣️ **Speaker Verification** (ECAPA-TDNN) - Identifies enrolled users by voice
- 🐣 **Speech Recognition** (Whisper) - Understands "Pay ₹500 to John"
- 💳 **Payment Flow** - Create intent → Voice confirm → Complete transaction
- ✅ **Liveness Detection** (Fine-tuned AASIST) - Your custom model for spoof detection

## 📁 Project Structure

```
vpay-flutter/
├── models/aasist/              # AASIST model architecture
├── services/                 # Business logic
│   ├── aasist_service.py     # Liveness check service
│   ├── aasist_inference.py   # Fine-tuned model wrapper
│   ├── speaker_service.py    # Speaker verification (ECAPA)
│   ├── whisper_service.py    # STT (Whisper)
│   └── payment_service.py    # Business logic
├── routes/                  # FastAPI endpoints
├── database/              # SQLite/PostgreSQL support
├── pretrained_models/     # Model weights
│   └── best_aasist_hinglish.pth  # ⭐ Your fine-tuned AASIST
└── main.py                # Entry point
```

## 🚀 Deployment

### Option 1: Hugging Face Spaces (Free)

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Create new Space → **Docker** → **CPU Basic (Free)**
3. Upload this repository or sync from GitHub
4. Set environment variables in **Settings → Secrets**:
   - `DATABASE_URL` - Your Supabase PostgreSQL connection string
5. Click **Factory Reboot** to deploy

### Option 2: Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📦 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /health` | Health check | Check if service is running |
| `POST /enroll` | Enroll voice | Register user's voice sample |
 unexpectedly| `POST /voice-pay/parse` | Parse intent | Convert speech to payment intent |
| `POST /pay/intent` | Create intent | Create a payment request |
| `POST /pay/intent/confirm` | Confirm payment | Voice confirmation + liveness check |
| `POST /verify` | Verify speaker | Check if voice matches enrolled speaker |
| `POST /transcribe` | Transcribe | Speech-to-text |

## 🔗 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(none)* | PostgreSQL connection string |
| `AASIST_MODEL_PATH` | `pretrained_models/best_aasist_hinglish.pth` | Fine-tuned model path |
| `LIVENESS_THRESHOLD` | `0.5` | Anti-spoofing threshold |
| `VERIFY_THRESHOLD` | `0.5` | Speaker verification threshold |
| `PRELOAD_ML_MODELS` | `false` | Preload ML models at startup |

## 🔧 Models Used

| Model | Source | Purpose | Size |
|-------|--------|---------|------|
| **AASIST** | Fine-tuned | Anti-spoofing / Liveness | **1.2MB** 🎯 |
| **ECAPA-TDNN** | SpeechBrain | Speaker verification | ~20MB |
| **Whisper** | OpenAI | Speech-to-text | ~150MB |

## 📔 Tech Stack

- **FastAPI** - Web framework
- **PyTorch** - ML inference
- **TensorFlow** - DeepFace face verification
- **SpeechBrain** - ECAPA-TDNN speaker model
- **SQLite/PostgreSQL** - Database

## 🎤 How It Works

```
User Says: "Pay ₹500 to John"
              ↓
    [AASIST Liveness Check]
    Is this real human speech? 🎯
              ↓ PASS
    [Speaker Verification (ECAPA)]
    Is this the enrolled user? 🗞️
              ↓ PASS
    [Whisper STT]
    "Pay Rs. 500 to John"
              ↓
        [Payment Confirmed] ✅
```

## 📝 License

MIT License - For educational purposes only. Not production-ready for real payments.

## 🗣️ Acknowledgment

- AASIST model from [Clova AI](https://github.com/clovaai/aasist)
- ECAPA-TDNN from [SpeechBrain](https://speechbrain.github.io/)
- Whisper from [OpenAI](https://openai.com/whisper)