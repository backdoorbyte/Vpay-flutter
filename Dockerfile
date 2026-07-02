# Dockerfile for VPay Backend on Railway/Render
# Railway sets PORT at runtime

FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/tmp/huggingface
ENV PRELOAD_ML_MODELS=false
ENV TF_USE_LEGACY_KERAS=1
ENV AASIST_MODEL_PATH=pretrained_models/best_aasist_hinglish.pth

# Expose port
EXPOSE 10000

# Health check using curl (uses PORT env var, defaults to 10000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-10000}/health || exit 1'

# Run the application (Railway sets PORT env var at runtime)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]