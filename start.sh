#!/bin/bash
set -e

# Clone or pull latest repo
if [ -d "$APP_DIR" ]; then
    echo "Pulling latest code..."
    cd "$APP_DIR"
    git pull
else
    echo "Cloning repo..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# Install Python dependencies (optional: if requirements changed)
pip install --no-cache-dir -r requirements.txt

# Start the app
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000