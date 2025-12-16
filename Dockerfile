# Production-ready Dockerfile for Soccer Slot Manager (clone-on-start)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    REPO_URL=https://github.com/abneits/soccer_slot_manager.git \
    APP_DIR=/app/git

# Install system dependencies (git, curl)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl bash && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run startup script
CMD ["/start.sh"]
