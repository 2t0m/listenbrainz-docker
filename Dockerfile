FROM python:3.9-slim

# Install system dependencies in one layer, with cleanup
RUN apt-get update && apt-get install -y \
    cron \
    ffmpeg \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install deemix via pip
RUN pip install --no-cache-dir deemix

# Set working directory
WORKDIR /app

# Copy only requirements.txt to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY listenbrainz_sync.py /app/
COPY config.json /app/config/config.json

# Set environment path
ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

# Set the entrypoint directly to Python script
ENTRYPOINT ["python3", "/app/listenbrainz_sync.py"]
