#!/usr/bin/env python3
"""VPay Backend Entry Point - handles PORT from environment."""

import os
import uvicorn

# Get PORT from environment, default to 8000
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    print(f"Starting VPay backend on port {port}...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )