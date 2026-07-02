# ============================================================
# VPay Backend - Hugging Face Spaces Deployment
# ============================================================
# This Dockerfile is optimized for Hugging Face Spaces free tier.
# HF Spaces provides: 16GB RAM, 2 vCPU, 50GB disk

FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies (ffmpeg, audio libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (excluding files in .dockerignore)
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HF_HOME=/tmp/huggingface
ENV PRELOAD_ML_MODELS=false
ENV TF_USE_LEGACY_KERAS=1
ENV AASIST_MODEL_PATH=pretrained_models/best_aasist_hinglish.pth

# Hugging Face Spaces default port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]