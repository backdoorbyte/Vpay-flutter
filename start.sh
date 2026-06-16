#!/bin/bash
set -e

# Ensure PORT is set (Railway default is 8000)
PORT=${PORT:-8000}

echo "Starting VPay backend on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"