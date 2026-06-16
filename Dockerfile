# Dockerfile for VPay Backend on Render
# Render uses Docker for deployment

FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgl1 \
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
ENV PORT=${PORT:-10000}

# Expose port (informational - actual port from PORT env var)
EXPOSE ${PORT}

# Health check (uses PORT env var)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get(f'http://localhost:${PORT}/health', timeout=5)" || exit 1

# Run the application - use shell form to expand PORT env var
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}