#!/bin/bash
set -e

# Ensure PORT is set from environment (Railway/Render/cloud platforms)
PORT=${PORT:-10000}

echo "Starting VPay backend on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"