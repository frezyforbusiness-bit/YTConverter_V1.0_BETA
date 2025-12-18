FROM python:3.12-slim

# Install system dependencies including browsers for cookie extraction
RUN apt-get update && apt-get install -y \
    ffmpeg \
    chromium \
    chromium-driver \
    firefox-esr \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for browser compatibility
# yt-dlp expects 'chrome' or 'chromium' to be available
RUN ln -s /usr/bin/chromium /usr/bin/chrome || true
RUN ln -s /usr/bin/chromium /usr/bin/google-chrome || true

# Set working directory
WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]

