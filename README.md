# VPay - Voice-Based Payment Authentication

A voice-based payment authentication system built with Flutter (frontend) and FastAPI (backend).

## Project Structure

```
vpay-flutter/
├── backend/        # FastAPI backend (Python)
│   ├── main.py           # API entry point
│   ├── requirements.txt # Python dependencies
│   ├── services/        # Business logic (AASIST, Whisper, etc.)
│   ├── routes/          # API endpoints
│   ├── database/        # SQLite/PostgreSQL
│   ├── models/          # ML model architectures
│   └── pretrained_models/ # Model weights (AASIST ECAPA-TDNN)
│
└── frontend/      # Flutter app (Dart)
    └── lib/       # Flutter source code
```

## Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Environment Variables:**
- `DATABASE_URL` - PostgreSQL connection string (for deployment)
- `AASIST_MODEL_PATH` - Path to fine-tuned AASIST model
- `LIVENESS_THRESHOLD` - Anti-spoofing threshold (default: 0.5)

## Frontend (Flutter)

```bash
cd frontend
flutter run
```

## Features

- 🎯 **Anti-Spoofing** - Fine-tuned AASIST model detects replay/voice conversion attacks
- 🗣️ **Speaker Verification** - ECAPA-TDNN identifies enrolled users
- 🐣 **Speech Recognition** - Whisper transcribes payment commands
- 💳 **Voice Payment** - Create and confirm payments with voice

## Deployment

### Hugging Face Spaces + Supabase

1. Create HF Space with Docker (CPU Basic free tier)
2. Set secrets: `DATABASE_URL`, `AASIST_MODEL_PATH`
3. Upload backend files from `backend/` folder
4. Connect to Supabase for database

### Render + PostgreSQL

See `backend/DEPLOY_RENDER.md`

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Flutter, Dart |
| Backend | FastAPI, Python 3.12 |
| Database | SQLite (local), PostgreSQL (production) |
| ML | PyTorch, TensorFlow, SpeechBrain, Whisper |

## License

MIT